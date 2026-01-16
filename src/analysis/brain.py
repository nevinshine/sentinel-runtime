import os
import sys

# --- CONFIGURATION ---
PIPE_REQ = "/tmp/sentinel_req"
PIPE_RESP = "/tmp/sentinel_resp"

# 🛡️ THE PROTECTED ZONE
# Any attempt to modify files in this folder will be BLOCKED.
PROTECTED_PATH = "sentinel_war_room/data"

def init_pipes():
    if not os.path.exists(PIPE_REQ):
        os.mkfifo(PIPE_REQ)
    if not os.path.exists(PIPE_RESP):
        os.mkfifo(PIPE_RESP)

def analyze_threat(syscall_verb, path):
    """
    The Core Policy Engine.
    Returns: True (ALLOW) or False (BLOCK)
    """
    
    # 1. Check Context: Is this happening in the Protected Zone?
    if PROTECTED_PATH in path:
        
        # 2. Check Intent: Is it destructive?
        # Ransomware relies on 'rename' (to add .enc) or 'unlink' (delete)
        if syscall_verb in ["rename", "unlink", "rmdir"]:
            print(f"\n[🧠 BRAIN] 🚨 RANSOMWARE ATTACK DETECTED!")
            print(f"          Target: {path}")
            print(f"          Action: {syscall_verb}")
            print(f"          Verdict: BLOCK ⛔")
            return False  # BLOCK
            
    # Default: Allow everything else (Normal OS noise)
    return True # ALLOW

def main():
    init_pipes()
    print(f"[🧠 BRAIN] Neural Engine Online.")
    print(f"[🧠 BRAIN] Protecting Zone: ~/{PROTECTED_PATH}")

    # Open pipes (Python opens Request as Read, Response as Write)
    # Note: verify permissions if this hangs
    fd_req = os.open(PIPE_REQ, os.O_RDONLY)
    fd_resp = os.open(PIPE_RESP, os.O_WRONLY)

    print("[🧠 BRAIN] Connected to Sentinel Core (C). Waiting for signals...")

    while True:
        # Read the raw message from C (e.g., "SYSCALL:rename:/home/user/data/file.txt")
        # We read byte-by-byte or small chunks to handle the stream
        # For simplicity in this demo, we read a chunk and strip
        try:
            raw_data = os.read(fd_req, 512).decode('utf-8').strip()
        except OSError:
            break
            
        if not raw_data:
            continue

        # Handle multiple messages coming in fast (split by newline if needed)
        messages = raw_data.split('\n')
        
        for msg in messages:
            if not msg.startswith("SYSCALL:"):
                continue

            parts = msg.split(":")
            if len(parts) < 3:
                continue

            # Parse: SYSCALL:verb:path
            verb = parts[1]
            path = parts[2]

            # --- DECIDE ---
            is_allowed = analyze_threat(verb, path)

            # --- RESPOND ---
            # '1' = Allow, '0' = Block
            response = b'1' if is_allowed else b'0'
            os.write(fd_resp, response)

if __name__ == "__main__":
    main()
