# src/analysis/state_machine.py
# RELEASE:  M3.6.0

import time
from enum import Enum, auto
from typing import Dict, Set
from dataclasses import dataclass

class ThreatState(Enum):
    IDLE = auto()
    SENSITIVE_FILE_OPENED = auto()
    SENSITIVE_DATA_HELD = auto()
    EXFILTRATION_ATTEMPT = auto()

SENSITIVE_TAGS = {
    "SENSITIVE_USER_FILE",
    "CRITICAL_AUTH",
    "SSH_PRIVATE_KEY",
    "ROOT_SENSITIVE"
}

@dataclass
class ProcessContext:
    pid: int
    state: ThreatState = ThreatState.IDLE
    has_read_sensitive: bool = False
    has_socket: bool = False
    last_activity: float = 0.0

    def __post_init__(self):
        self.last_activity = time.time()


class ExfiltrationDetector:
    """
    Heuristic State Machine for detecting data exfiltration.
    Uses Taint Analysis to track sensitive data across process boundaries (pipes).

    Updated M3.2: Handles FD duplication (dup/dup2) to prevent evasion.
    """

    PROCESS_TIMEOUT_SECONDS = 30.0  # Reset individual process state after inactivity
    PIPELINE_TIMEOUT_SECONDS = 5.0  # Reset global pipeline taint (pipes are fast)

    def __init__(self):
        self.processes: Dict[int, ProcessContext] = {}

        # Standard pipe FDs (stdin, stdout, stderr)
        # We make this an instance set so we can dynamically add duped FDs
        self.PIPE_FDS = {0, 1, 2}

        # Cross-process taint tracking
        self.sensitive_data_in_pipeline = False
        self.pipeline_taint_time = 0.0
        self.tainted_pids: Set[int] = set()

    def _get_context(self, pid: int) -> ProcessContext:
        if pid not in self.processes:
            self.processes[pid] = ProcessContext(pid=pid)
        return self.processes[pid]

    def process_event(self, pid: int, syscall: str, args: dict, semantic_tag: str = None) -> str:
        ctx = self._get_context(pid)
        now = time.time()

        # === HOUSEKEEPING: Timeout Resets ===

        # Reset individual process state after inactivity
        if now - ctx.last_activity > self.PROCESS_TIMEOUT_SECONDS:
            self._reset_state(ctx)
        ctx.last_activity = now

        # Reset global pipeline taint after timeout (prevents false positives)
        if self.sensitive_data_in_pipeline and (now - self.pipeline_taint_time > self.PIPELINE_TIMEOUT_SECONDS):
            self.sensitive_data_in_pipeline = False
            self.tainted_pids.clear()

        # === STATE TRANSITIONS ===

        # STAGE 1: OPEN SENSITIVE FILE
        if syscall in ["open", "openat"]:
            if semantic_tag in SENSITIVE_TAGS:
                ctx.state = ThreatState.SENSITIVE_FILE_OPENED
                return f"MONITOR: Opened sensitive file ({semantic_tag})"

        # STAGE 2: READ
        elif syscall == "read":
            fd = int(args.get("fd", -1))

            # If we previously opened a sensitive file, this read loads the data
            if ctx.state == ThreatState.SENSITIVE_FILE_OPENED:
                ctx.state = ThreatState.SENSITIVE_DATA_HELD
                ctx.has_read_sensitive = True
                return "MONITOR: Sensitive data loaded into memory"

            # Cross-process: reading from stdin while pipeline is tainted
            if fd == 0 and self.sensitive_data_in_pipeline:
                ctx.state = ThreatState.SENSITIVE_DATA_HELD
                ctx.has_read_sensitive = True
                self.tainted_pids.add(pid)
                return "MONITOR: Received tainted data via pipe"

        # STAGE 3: RESOURCE DUPLICATION (EVASION PROTECTION)
        elif syscall in ["dup", "dup2", "dup3"]:
            old_fd = int(args.get("fd", -1))
            new_fd = int(args.get("ret", -1)) # Success return value is the new FD

            # If the old FD was a pipe, the new one acts as a pipe too.
            # This catches: dup2(stdout, 99) -> write(99, data)
            if new_fd >= 0 and old_fd in self.PIPE_FDS:
                self.PIPE_FDS.add(new_fd)
                return f"MONITOR: FD {old_fd} duplicated to {new_fd} - Tracking alias"

        # STAGE 4: SOCKET CREATION
        elif syscall == "socket":
            ctx.has_socket = True
            return "MONITOR: Socket created"

        # STAGE 5: SOCKET CONNECT
        elif syscall == "connect":
            ctx.has_socket = True
            return "MONITOR: Socket connected"

        # STAGE 6: WRITE - THE CRITICAL DECISION POINT
        elif syscall in ["write", "sendto", "sendmsg"]:
            fd = int(args.get("fd", -1))

            # Case A: Writing sensitive data to stdout/pipe (cross-process setup)
            if fd in self.PIPE_FDS and ctx.has_read_sensitive:
                self.sensitive_data_in_pipeline = True
                self.pipeline_taint_time = now
                return "MONITOR: ⚠️ Sensitive data written to pipe - tracking downstream"

            # Case B: Direct exfiltration (same process has sensitive data + socket)
            # Note: We assume writing to a NON-PIPE FD implies network/file exfil intent
            if fd not in self.PIPE_FDS and ctx.has_read_sensitive and ctx.has_socket:
                ctx.state = ThreatState.EXFILTRATION_ATTEMPT
                return "BLOCK"

            # Case C: Cross-process exfiltration (writing to socket while pipeline hot)
            if fd not in self.PIPE_FDS and self.sensitive_data_in_pipeline:
                if ctx.has_socket or pid in self.tainted_pids:
                    ctx.state = ThreatState.EXFILTRATION_ATTEMPT
                    # Reset pipeline state after blocking
                    self.sensitive_data_in_pipeline = False
                    self.tainted_pids.clear()
                    return "BLOCK"

        # STAGE 7: CLOSE
        elif syscall == "close":
            fd = int(args.get("fd", -1))
            # Optional: Remove FD from set if we want to be strict,
            # but keeping it is safer for FDs reused by shells.
            pass

        return "ALLOW"

    def _reset_state(self, ctx: ProcessContext):
        """Reset a single process context to clean state."""
        ctx.state = ThreatState.IDLE
        ctx.has_read_sensitive = False
        ctx.has_socket = False