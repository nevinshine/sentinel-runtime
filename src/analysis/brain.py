import os
import sys
import json
import select
import signal
import subprocess
from semantic import SemanticMapper
from state_machine import ExfiltrationDetector

# src/analysis/brain.py
# RELEASE: Milestone 4.0 (Unified Defense: Seccomp + Integrity + Auto-DLP)

# --- CONFIGURATION ---
REQ_PIPE = os.environ.get("SENTINEL_PIPE_REQ", "/tmp/sentinel_req")
RESP_PIPE = os.environ.get("SENTINEL_PIPE_RESP", "/tmp/sentinel_resp")

# Hyperion Integration
HYPERION_CONFIG = "signatures.txt"

# ANSI Colors
COLOR_RED     = "\033[1;31m"
COLOR_GREEN   = "\033[1;32m"
COLOR_YELLOW  = "\033[1;33m"
COLOR_CYAN    = "\033[1;36m"
COLOR_GRAY    = "\033[90m"
COLOR_RESET   = "\033[0m"

# --- TRUSTED BINARIES (The "White List") ---
# These tools are allowed to read sensitive data and talk to local sockets
TRUSTED_TALKERS = ["ls", "dir", "ps", "top", "systemd", "dbus-daemon", "gnome-shell"]

def init_pipes():
    if not os.path.exists(REQ_PIPE): os.mkfifo(REQ_PIPE)
    if not os.path.exists(RESP_PIPE): os.mkfifo(RESP_PIPE)

def get_process_name(pid):
    """
    Real-World Context: Look up the process name from the OS.
    """
    try:
        with open(f"/proc/{pid}/comm", "r") as f:
            return f.read().strip()
    except:
        return "unknown"

def update_hyperion_firewall(keyword):
    """
    BRIDGE: Tell Hyperion (XDP) to block this keyword on the network.
    """
    # 1. Clean the keyword (remove paths and extensions)
    clean_sig = os.path.splitext(os.path.basename(keyword))[0]
    
    if len(clean_sig) < 4: return # Too short to be a unique signature

    # 2. Check if already blocked to avoid IO spam
    try:
        # Ensure file exists
        if not os.path.exists(HYPERION_CONFIG):
            with open(HYPERION_CONFIG, "w") as f: f.write("")

        with open(HYPERION_CONFIG, "r+") as f:
            lines = [l.strip() for l in f.readlines()]
            if clean_sig in lines: return # Already protected
            
            # 3. Add to Firewall
            f.write(f"\n{clean_sig}")
            print(f"{COLOR_CYAN}[BRIDGE] 🛡️  Auto-DLP: Added '{clean_sig}' to Network Blocklist.{COLOR_RESET}")
            
    except Exception as e:
        print(f"[ERROR] Bridge failed: {e}")

def parse_message(raw_data: str) -> dict:
    try:
        msg = json.loads(raw_data)
        # Ensure default keys exist for legacy logic, but keep extra keys (cmd, flags)
        for k in ("verb", "path", "pid", "fd", "ret"):
            if k not in msg:
                msg[k] = "" if k in ("verb", "path") else -1
        return msg
    except:
        return None

def main():
    os.system("clear")
    print(f"{COLOR_GREEN}╔══════════════════════════════════════════════════════════════╗{COLOR_RESET}")
    print(f"{COLOR_GREEN}║  SENTINEL NEURAL ENGINE v4.0 - UNIFIED DEFENSE GRID          ║{COLOR_RESET}")
    print(f"{COLOR_GREEN}╚══════════════════════════════════════════════════════════════╝{COLOR_RESET}")
    print()

    mapper = SemanticMapper()
    detector = ExfiltrationDetector()
    init_pipes()

    print(f"{COLOR_YELLOW}+ [WAIT] Waiting for Sentinel Kernel Link...{COLOR_RESET}")
    f_req = open(REQ_PIPE, "r")
    f_resp = open(RESP_PIPE, "w")
    print(f"{COLOR_GREEN}+ [INFO] Sentinel Link Established.{COLOR_RESET}")
    print()
    print("-" * 115)
    print(f"{'VERDICT':<10} | {'PROC':<10} | {'ACTION':<10} | {'STATE':<22} | {'TAG':<22} | {'TARGET'}")
    print("-" * 115)

    # Security Policies
    sensitive_tags = ["SENSITIVE_USER_FILE", "CRITICAL_AUTH", "SSH_PRIVATE_KEY", "ROOT_SENSITIVE"]
    destructive_verbs = ["write", "unlink", "unlinkat", "rmdir", "rename"]

    while True:
        try:
            rlist, _, _ = select.select([f_req], [], [], 1.0)
            if not rlist: continue

            raw_data = f_req.readline()
            if not raw_data: break

            msg = parse_message(raw_data)
            if not msg: continue

            verb, path, pid = msg["verb"], msg["path"], msg["pid"]
            
            # 1. GET CONTEXT
            proc_name = get_process_name(pid)

            # 2. SEMANTIC ANALYSIS
            concept = "N/A"
            if verb in ["open", "openat", "unlink", "unlinkat", "rmdir", "rename", "mkdir", "execve"]:
                concept = mapper.classify(path)

            # 3. STATE MACHINE ANALYSIS
            args = {"fd": str(msg["fd"]), "ret": str(msg["ret"])}
            state_verdict = detector.process_event(pid, verb, args, concept)
            ctx = detector._get_context(pid)
            current_state = ctx.state.name

            # --- AUTO-DLP TRIGGER ---
            if concept in sensitive_tags and verb in ["open", "openat"]:
                update_hyperion_firewall(path)

            # --- DECISION LOGIC ---
            blocked = False
            block_reason = ""

            # [NEW] PRIORITY 0: ARCHITECTURAL DEFENSE (Ghost/Invisible/Race)
            if verb == "bpf":
                blocked = True
                block_reason = "KERNEL_ATTACK"
                concept = "eBPF_INJECTION"
            
            elif verb == "mprotect" and "PROT_EXEC" in msg.get("flags", ""):
                blocked = True
                block_reason = "FILELESS_MALWARE"
                concept = "MEMORY_WX_VIOLATION"

            elif verb == "openat" and ("/proc/sys" in path or "/sys/kernel" in path):
                blocked = True
                block_reason = "CONTAINER_ESCAPE"
                concept = "CRITICAL_HOST_PATH"

            # PRIORITY 1: EXFILTRATION (With Trust Filter)
            elif state_verdict == "BLOCK":
                # FILTER: Trust system binaries talking to local sockets
                if proc_name in TRUSTED_TALKERS and verb in ["sendto", "connect", "socket"]:
                    blocked = False
                else:
                    blocked = True
                    block_reason = "EXFILTRATION"

            # PRIORITY 2: INTEGRITY SHIELD (Anti-Ransomware)
            elif verb in destructive_verbs and concept in sensitive_tags:
                blocked = True
                block_reason = "INTEGRITY"

            # PRIORITY 3: USB EXFILTRATION TRAP
            elif current_state == "SENSITIVE_DATA_HELD" and verb == "write":
                 if path.startswith("/media") or path.startswith("/mnt") or "fake_usb" in path:
                      blocked = True
                      block_reason = "USB_EXFILTRATION"

            # PRIORITY 4: HONEYPOT (Deception)
            elif "honeypot" in path.lower() or "secret_passwords" in path.lower():
                blocked = True
                block_reason = "HONEYPOT"

            # --- EXECUTE & LOG ---
            if blocked:
                f_resp.write("0")
                f_resp.flush()
                print(f"{COLOR_RED}{'BLOCK':<10} | {proc_name:<10} | {verb:<10} | {block_reason:<22} | {concept:<22} | {path}{COLOR_RESET}")
                
                if block_reason == "KERNEL_ATTACK":
                    print(f"{COLOR_RED}  └── ☠️  CRITICAL: INVISIBLE ENEMY TRAPPED! Kernel Integrity Saved.{COLOR_RESET}")
                elif block_reason == "CONTAINER_ESCAPE":
                    print(f"{COLOR_RED}  └── ☠️  CRITICAL: RUNC RACE CONDITION NEUTRALIZED!{COLOR_RESET}")
                elif block_reason == "EXFILTRATION":
                     print(f"{COLOR_RED}  └── ⚠️  DATA LEAK BLOCKED! Process '{proc_name}' attempted network exfiltration.{COLOR_RESET}")

            else:
                f_resp.write("1")
                f_resp.flush()
                
                # --- NOISE REDUCTION ---
                if concept in ["SHARED_LIBRARY", "PROC_FS", "DEVICE_NULL"]: continue
                if verb == "write" and path == "": continue 

                # Color coding
                color = COLOR_RESET
                if current_state == "SENSITIVE_DATA_HELD": color = COLOR_YELLOW
                if concept in sensitive_tags: color = COLOR_CYAN

                disp_path = path if len(path) <= 30 else path[:27] + "..."
                print(f"{color}{'ALLOW':<10} | {proc_name:<10} | {verb:<10} | {current_state:<22} | {concept: <22} | {disp_path}{COLOR_RESET}")

        except KeyboardInterrupt:
            print(f"\n{COLOR_YELLOW}+ [INFO] Shutting down Sentinel...{COLOR_RESET}")
            break
        except Exception as e:
            print(f"{COLOR_RED}[ERROR] {e}{COLOR_RESET}")
            break

    f_req.close()
    f_resp.close()

if __name__ == "__main__":
    main()
