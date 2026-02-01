# src/analysis/brain.py
# RELEASE:  Milestone 3.1 (Exfiltration State Machine)

import os
import sys
import time
import select
from semantic import SemanticMapper
from state_machine import ExfiltrationDetector  # NEW: Import state machine

# --- CONFIGURATION ---
REQ_PIPE = os.environ.get("SENTINEL_PIPE_REQ", "/tmp/sentinel_req")
RESP_PIPE = os.environ.get("SENTINEL_PIPE_RESP", "/tmp/sentinel_resp")

# ANSI Colors for Professional Logging
COLOR_RED     = "\033[1;31m"
COLOR_GREEN   = "\033[1;32m"
COLOR_YELLOW  = "\033[1;33m"
COLOR_CYAN    = "\033[1;36m"
COLOR_GRAY    = "\033[90m"
COLOR_RESET   = "\033[0m"

def init_pipes():
    if not os.path.exists(REQ_PIPE):
        os.mkfifo(REQ_PIPE)
    if not os.path.exists(RESP_PIPE):
        os.mkfifo(RESP_PIPE)

def parse_message(raw_data:  str) -> dict:
    """
    Parse the IPC message from the C engine. Now expects JSON for robust parsing.
    Falls back to legacy colon-split if JSON fails (for backward compatibility).
    """
    import json
    try:
        # Try JSON first
        msg = json.loads(raw_data)
        # Ensure required fields exist
        for k in ("verb", "path", "pid", "fd", "ret"):
            if k not in msg:
                msg[k] = "" if k in ("verb", "path") else -1
        return msg
    except Exception:
        # Legacy fallback: colon-split
        result = {
            "verb": "",
            "path": "",
            "pid": 0,
            "fd": -1,
            "ret": -1
        }
        parts = raw_data.strip().split(":")
        if len(parts) < 3:
            return None
        result["verb"] = parts[1]
        result["path"] = parts[2].strip()
        for part in parts[3:]:
            part = part.strip()
            if "=" in part:
                key, val = part.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key == "pid":
                    result["pid"] = int(val) if val.lstrip('-').isdigit() else 0
                elif key == "fd":
                    result["fd"] = int(val) if val.lstrip('-').isdigit() else -1
                elif key == "ret":
                    result["ret"] = int(val) if val.lstrip('-').isdigit() else -1
        return result

def main():
    os.system("clear")
    print(f"{COLOR_GREEN}╔══════════════════════════════════════════════════════════════╗{COLOR_RESET}")
    print(f"{COLOR_GREEN}║  SENTINEL NEURAL ENGINE v3.4 - Exfiltration Detection Mode   ║{COLOR_RESET}")
    print(f"{COLOR_GREEN}╚══════════════════════════════════════════════════════════════╝{COLOR_RESET}")
    print()

    # Initialize the Knowledge Base
    mapper = SemanticMapper()
    print(f"{COLOR_GREEN}+ [INFO] Semantic Knowledge Base Loaded.{COLOR_RESET}")

    # NEW: Initialize the State Machine
    detector = ExfiltrationDetector()
    print(f"{COLOR_GREEN}+ [INFO] Exfiltration State Machine Armed.{COLOR_RESET}")

    init_pipes()

    print(f"{COLOR_YELLOW}+ [WAIT] Waiting for Sentinel Kernel Link...{COLOR_RESET}")
    f_req = open(REQ_PIPE, "r")
    f_resp = open(RESP_PIPE, "w")
    print(f"{COLOR_GREEN}+ [INFO] Sentinel Link Established.{COLOR_RESET}")
    print()
    print("-" * 95)
    print(f"{'VERDICT':<10} | {'PID':<8} | {'ACTION':<10} | {'STATE':<22} | {'TAG':<18} | {'TARGET'}")
    print("-" * 95)

    # Destructive verbs (existing M3.0 logic)
    destructive_verbs = ["unlink", "unlinkat", "rmdir", "rename"]

    # Sensitive tags for blocking
    sensitive_tags = ["SENSITIVE_USER_FILE", "CRITICAL_AUTH", "SSH_PRIVATE_KEY", "ROOT_SENSITIVE"]

    while True:
        try:
            # Use select to avoid blocking forever
            rlist, _, _ = select.select([f_req], [], [], 1.0)
            if not rlist:
                continue  # No data yet, loop back

            raw_data = f_req.readline()
            if not raw_data:
                break

            # Parse the enhanced message format
            msg = parse_message(raw_data)
            if msg is None:
                continue

            verb = msg["verb"]
            path = msg["path"]
            pid = msg["pid"]
            fd = msg["fd"]
            ret = msg["ret"]

            # --- PHASE M3.0: SEMANTIC ANALYSIS ---
            # Classify the path (only meaningful for file operations)
            concept = "N/A"
            if verb in ["open", "openat", "unlink", "unlinkat", "rmdir", "rename", "mkdir", "execve"]:
                concept = mapper.classify(path)

            # --- PHASE M3.1: STATE MACHINE ANALYSIS ---
            # Build args dict for state machine
            args = {
                "fd": str(fd),
                "ret": str(ret)
            }

            # Process through state machine
            state_verdict = detector.process_event(
                pid=pid,
                syscall=verb,
                args=args,
                semantic_tag=concept
            )

            # Get current state for logging
            ctx = detector._get_context(pid)
            current_state = ctx.state. name

            # --- DECISION LOGIC ---
            blocked = False
            block_reason = ""

            # Priority 1: State Machine BLOCK (Exfiltration detected!)
            if state_verdict == "BLOCK":
                blocked = True
                block_reason = "EXFILTRATION"

            # Priority 2: INTEGRITY SHIELD (Aggressive Write Blocking)
            # Rule: NEVER allow modification of sensitive files.
            elif verb in ["write", "unlink", "unlinkat", "rmdir", "rename"] and concept in sensitive_tags:
                blocked = True
                block_reason = "INTEGRITY_VIOLATION"

            # Priority 3: HONEYPOT (Aggressive Read Blocking)
            # Rule: If anyone touches a 'bait' file, kill them.
            elif "honeypot" in path.lower() or "secret_passwords" in path.lower():
                blocked = True
                block_reason = "HONEYPOT_TRIGGERED"

            # --- EXECUTE & LOG ---
            if blocked:
                # Send BLOCK ('0')
                f_resp.write("0")
                f_resp.flush()

                # Red alert for blocks
                print(f"{COLOR_RED}{'BLOCK':<10} | {pid:<8} | {verb:<10} | {current_state:<22} | {concept:<18} | {path}{COLOR_RESET}")

                # Extra alert for exfiltration
                if block_reason == "EXFILTRATION":
                    print(f"{COLOR_RED}  └── ⚠️  EXFILTRATION ATTEMPT BLOCKED!  Sensitive data was about to leave via network.{COLOR_RESET}")

            else:
                # Send ALLOW ('1')
                f_resp.write("1")
                f_resp.flush()

                # Color coding based on state/verdict
                color = COLOR_RESET

                if state_verdict. startswith("MONITOR"):
                    color = COLOR_YELLOW  # Yellow for monitored (suspicious but allowed)
                elif concept in ["SHARED_LIBRARY", "PROC_FS", "DEVICE_TTY", "DEVICE_NULL", "TEMP_FILE"]:
                    color = COLOR_GRAY    # Gray for noise
                elif concept in sensitive_tags:
                    color = COLOR_CYAN    # Cyan for sensitive file access (not blocked)

                # Truncate long paths for display
                display_path = path if len(path) <= 40 else path[:37] + "..."

                print(f"{color}{'ALLOW':<10} | {pid:<8} | {verb:<10} | {current_state:<22} | {concept: <18} | {display_path}{COLOR_RESET}")

        except KeyboardInterrupt:
            print(f"\n{COLOR_YELLOW}+ [INFO] Shutting down Neural Engine...{COLOR_RESET}")
            break
        except Exception as e:
            print(f"{COLOR_RED}[ERROR] {e}{COLOR_RESET}")
            import traceback
            traceback.print_exc()
            break

    f_req.close()
    f_resp.close()
    print(f"{COLOR_GREEN}+ [INFO] Sentinel Neural Engine Offline.{COLOR_RESET}")

if __name__ == "__main__":
    main()