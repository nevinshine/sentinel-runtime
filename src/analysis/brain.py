import os
import sys

# --- CONFIGURATION ---
REQ_PIPE = "/tmp/sentinel_req"
RESP_PIPE = "/tmp/sentinel_resp"

# ANSI Colors for Professional Logging
COLOR_RED = "\033[1;31m"
COLOR_GREEN = "\033[1;32m"
COLOR_RESET = "\033[0m"

# Policy Configuration
# Set to "" to protect everything, or a specific path like "/secret_data"
PROTECTED_PATH = "" 

def init_pipes():
    if not os.path.exists(REQ_PIPE):
        os.mkfifo(REQ_PIPE)
    if not os.path.exists(RESP_PIPE):
        os.mkfifo(RESP_PIPE)

def analyze_threat(syscall_verb, path):
    """
    The Core Policy Engine.
    Returns: True (ALLOW) or False (BLOCK)
    """
    # 1. Scope Check
    if PROTECTED_PATH not in path:
        return True

    # 2. Intent Check: Is it destructive?
    # We block 'unlink' (file del), 'rmdir' (dir del), and 'rename' (ransomware)
    if syscall_verb in ["unlink", "rmdir", "rename"]:
        return False # BLOCK
        
    return True # ALLOW

def main():
    print(f"[INFO] Neural Engine Online.")
    init_pipes()

    # Open pipes: Read Request first, then Write Response
    print("[INFO] Connecting to Request Channel...")
    f_req = open(REQ_PIPE, "r")
    
    print("[INFO] Connecting to Response Channel...")
    f_resp = open(RESP_PIPE, "w")

    print("[INFO] Sentinel Link Established. Monitoring...")

    while True:
        try:
            # Read line-by-line (Stable Protocol)
            raw_data = f_req.readline()
            if not raw_data: break # EOF
            
            cmd = raw_data.strip()
            
            # Parse Protocol: SYSCALL:verb:path
            parts = cmd.split(":")
            if len(parts) < 3: continue
            
            verb = parts[1]
            path = parts[2]

            # DECIDE
            if analyze_threat(verb, path):
                # ALLOW
                f_resp.write("1")
                f_resp.flush()
                print(f"[LOG]   Action: {verb} | Path: {path}")
            else:
                # BLOCK
                f_resp.write("0")
                f_resp.flush()
                print(f"{COLOR_RED}[ALERT] BLOCKED THREAT: {verb} -> {path}{COLOR_RESET}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            break

    # Cleanup
    f_req.close()
    f_resp.close()
    print("\n[INFO] Session Terminated.")

if __name__ == "__main__":
    main()
