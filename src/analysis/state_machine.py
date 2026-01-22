# src/analysis/state_machine.py
# RELEASE:  M3.1.3 - Production Ready with Pipeline Timeout

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
    state: ThreatState = ThreatState. IDLE
    has_read_sensitive: bool = False
    has_socket:  bool = False
    last_activity: float = 0.0

    def __post_init__(self):
        self.last_activity = time.time()


class ExfiltrationDetector:
    """
    Heuristic State Machine for detecting data exfiltration.
    Uses Taint Analysis to track sensitive data across process boundaries (pipes).

    Detection Pattern:
      1. Process opens sensitive file (CRITICAL_AUTH, etc.)
      2. Process reads from that file (data now in memory)
      3. Process writes to network socket → BLOCK (same-process exfil)

      OR (cross-process via pipe):

      1. Process A opens sensitive file, reads it
      2. Process A writes to stdout (pipe) → Pipeline becomes "tainted"
      3. Process B reads from stdin (receives tainted data)
      4. Process B writes to network socket → BLOCK (pipe-based exfil)
    """

    PROCESS_TIMEOUT_SECONDS = 30.0  # Reset individual process state after inactivity
    PIPELINE_TIMEOUT_SECONDS = 5.0  # Reset global pipeline taint (pipes are fast)
    PIPE_FDS = {0, 1, 2}  # stdin, stdout, stderr

    def __init__(self):
        self.processes: Dict[int, ProcessContext] = {}

        # Cross-process taint tracking
        self.sensitive_data_in_pipeline = False
        self.pipeline_taint_time = 0.0
        self.tainted_pids: Set[int] = set()

    def _get_context(self, pid:  int) -> ProcessContext:
        if pid not in self.processes:
            self.processes[pid] = ProcessContext(pid=pid)
        return self.processes[pid]

    def process_event(self, pid: int, syscall: str, args: dict, semantic_tag: str = None) -> str:
        ctx = self._get_context(pid)
        now = time.time()

        # === HOUSEKEEPING:  Timeout Resets ===

        # Reset individual process state after inactivity
        if now - ctx.last_activity > self. PROCESS_TIMEOUT_SECONDS:
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
                return f"MONITOR:  Opened sensitive file ({semantic_tag})"

        # STAGE 2: READ
        elif syscall == "read":
            fd = int(args. get("fd", -1))

            # If we previously opened a sensitive file, this read loads the data
            if ctx.state == ThreatState.SENSITIVE_FILE_OPENED:
                ctx.state = ThreatState. SENSITIVE_DATA_HELD
                ctx.has_read_sensitive = True
                return "MONITOR:  Sensitive data loaded into memory"

            # Cross-process:  reading from stdin while pipeline is tainted
            if fd == 0 and self.sensitive_data_in_pipeline:
                ctx. state = ThreatState. SENSITIVE_DATA_HELD
                ctx.has_read_sensitive = True
                self.tainted_pids.add(pid)
                return "MONITOR: Received tainted data via pipe"

        # STAGE 3: SOCKET CREATION
        elif syscall == "socket":
            ctx.has_socket = True
            return "MONITOR: Socket created"

        # STAGE 4: SOCKET CONNECT
        elif syscall == "connect":
            ctx.has_socket = True
            return "MONITOR: Socket connected"

        # STAGE 5: WRITE - THE CRITICAL DECISION POINT
        elif syscall in ["write", "sendto", "sendmsg"]:
            fd = int(args.get("fd", -1))

            # Case A: Writing sensitive data to stdout/pipe (cross-process setup)
            if fd in self. PIPE_FDS and ctx. has_read_sensitive:
                self.sensitive_data_in_pipeline = True
                self.pipeline_taint_time = now
                return "MONITOR: ⚠️ Sensitive data written to pipe - tracking downstream"

            # Case B: Direct exfiltration (same process has sensitive data + socket)
            if fd not in self.PIPE_FDS and ctx.has_read_sensitive and ctx.has_socket:
                ctx.state = ThreatState. EXFILTRATION_ATTEMPT
                return "BLOCK"

            # Case C: Cross-process exfiltration (writing to socket while pipeline hot)
            if fd not in self.PIPE_FDS and self.sensitive_data_in_pipeline:
                if ctx.has_socket or pid in self.tainted_pids:
                    ctx.state = ThreatState.EXFILTRATION_ATTEMPT
                    # Reset pipeline state after blocking
                    self.sensitive_data_in_pipeline = False
                    self.tainted_pids.clear()
                    return "BLOCK"

        # STAGE 6: CLOSE (no state change needed)
        elif syscall == "close":
            pass

        return "ALLOW"

    def _reset_state(self, ctx: ProcessContext):
        """Reset a single process context to clean state."""
        ctx.state = ThreatState.IDLE
        ctx.has_read_sensitive = False
        ctx.has_socket = False