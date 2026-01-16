import os
import sys

# --- CONFIGURATION ---
PIPE_REQ = "/tmp/sentinel_req"
PIPE_RESP = "/tmp/sentinel_resp"

# 🛡️ THE FIX: Match simply "data" to catch relative paths
PROTECTED_PATH = "data"

def init_pipes():
    if not os.path.exists(PIPE_REQ):
        os.mkfifo(PIPE_REQ)
    if not os.path.exists(PIPE_RESP):
        os.mkfifo(PIPE_RESP)

def analyze_threat(syscall_verb, path):
    # DEBUG PRINT: Show me everything!
    print(f"[👀 INSPECT] Verb: {syscall_verb} | Path: {path}")

    # 1. Check Context
    if PROTECTED_PATH in path:
        # 2. Check Intent
        if syscall_verb in ["rename", "unlink", "rmdir", "mkdir"]:
            print(f"    🚨 BLOCKING RANSOMWARE on: {path}")
            return False  # BLOCK
            
    print(f"    ✅ Allowed (Not a threat)")
    return True # ALLOW

def main():
    init_pipes()
    print(f"[🧠 BRAIN] Debug Mode Online. Protecting keyword: '{PROTECTED_PATH}'")
    print(f"[🧠 BRAIN] Waiting for signals...")

    fd_req = os.open(PIPE_REQ, os.O_RDONLY)
    fd_resp = os.open(PIPE_RESP, os.O_WRONLY)

    while True:
        try:
            raw_data = os.read(fd_req, 512).decode('utf-8').strip()
        except OSError:
            break
            
        if not raw_data:
            continue

        messages = raw_data.split('\n')
        for msg in messages:
            if not msg.startswith("SYSCALL:"):
                continue

            parts = msg.split(":")
            if len(parts) < 3:
                continue

            verb = parts[1]
            path = parts[2]

            is_allowed = analyze_threat(verb, path)

            response = b'1' if is_allowed else b'0'
            os.write(fd_resp, response)

if __name__ == "__main__":
    main()
