import os
import sys
import time
from semantic import SemanticMapper  # Import the new M3 module

# --- CONFIGURATION ---
REQ_PIPE = "/tmp/sentinel_req"
RESP_PIPE = "/tmp/sentinel_resp"

# ANSI Colors for Professional Logging
COLOR_RED     = "\033[1;31m"
COLOR_GREEN   = "\033[1;32m"
COLOR_YELLOW  = "\033[1;33m"
COLOR_CYAN    = "\033[1;36m"
COLOR_RESET   = "\033[0m"

def init_pipes():
    if not os.path.exists(REQ_PIPE):
        os.mkfifo(REQ_PIPE)
    if not os.path.exists(RESP_PIPE):
        os.mkfifo(RESP_PIPE)

def main():
    os.system("clear")
    print(f"{COLOR_GREEN}+ [INFO] Neural Engine Online (M3.0 Cognitive Mode).{COLOR_RESET}")

    # Initialize the Knowledge Base
    mapper = SemanticMapper()
    print(f"{COLOR_GREEN}+ [INFO] Semantic Knowledge Base Loaded.{COLOR_RESET}")

    init_pipes()

    print(f"{COLOR_YELLOW}+ [WAIT] Waiting for Sentinel Kernel Link...{COLOR_RESET}")
    f_req = open(REQ_PIPE, "r")
    f_resp = open(RESP_PIPE, "w")
    print(f"{COLOR_GREEN}+ [INFO] Sentinel Link Established.{COLOR_RESET}")
    print("-" * 75)
    print(f"{'VERDICT':<10} | {'ACTION':<10} | {'SEMANTIC TAG':<20} | {'PATH'}")
    print("-" * 75)

    destructive_verbs = ["unlink", "unlinkat", "rmdir", "rename"]

    while True:
        try:
            raw_data = f_req.readline()
            if not raw_data: break

            cmd = raw_data.strip()
            parts = cmd.split(":")
            if len(parts) < 3: continue

            verb = parts[1]
            path = parts[2]

            # --- PHASE M3: SEMANTIC ANALYSIS ---
            # 1. Classify the raw path into a Concept
            concept = mapper.classify(path)

            # 2. DECISION LOGIC (Behavioral Policy)
            # Rule: Block destructive actions on SENSITIVE or CRITICAL tags
            blocked = False

            if verb in destructive_verbs:
                if concept in ["SENSITIVE_USER_FILE", "CRITICAL_AUTH", "SSH_PRIVATE_KEY", "ROOT_SENSITIVE"]:
                    blocked = True

            # 3. EXECUTE & LOG
            if blocked:
                # Send BLOCK ('0')
                f_resp.write("0")
                f_resp.flush()
                print(f"{COLOR_RED}{'BLOCK':<10} | {verb:<10} | {concept:<20} | {path}{COLOR_RESET}")
            else:
                # Send ALLOW ('1')
                f_resp.write("1")
                f_resp.flush()

                # Dim the logs for "Noise" concepts to reduce clutter
                color = COLOR_RESET
                if concept in ["SHARED_LIBRARY", "PROC_FS", "DEVICE_TTY"]:
                    color = "\033[90m" # Gray for noise

                print(f"{color}{'ALLOW':<10} | {verb:<10} | {concept:<20} | {path}{COLOR_RESET}")

        except KeyboardInterrupt:
            print(f"\n{COLOR_YELLOW}+ [INFO] Shutting down...{COLOR_RESET}")
            break
        except Exception as e:
            print(f"{COLOR_RED}[ERROR] {e}{COLOR_RESET}")
            break

    f_req.close()
    f_resp.close()

if __name__ == "__main__":
    main()