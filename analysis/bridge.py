# analysis/bridge.py
import os
import time
from brain import WiSARD  # <--- IMPORT THE BRAIN

PIPE_PATH = "/tmp/sentinel_ipc"

def start_listener():
    # 1. Initialize the AI
    cortex = WiSARD()
    print("[INIT] Neural Cortex Online.")
    
    # 2. Fast Training (The "Base Knowledge")
    # We teach it that 'mkdir' and 'access' are safe for this demo.
    print("[INIT] Loading base patterns...")
    cortex.train("mkdir")
    cortex.train("access")
    cortex.train("openat")
    print("[INIT] ✅ Training Complete.")

    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)
    
    print(f"[BRIDGE] Listening on {PIPE_PATH}...")

    with open(PIPE_PATH, "r") as pipe:
        while True:
            line = pipe.readline()
            if not line: break
            
            # Data Format: "SYSCALL:mkdir:filename"
            try:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    call_type = parts[1] # e.g., "mkdir"
                    arg_val = parts[2] if len(parts) > 2 else ""

                    # 3. ASK THE BRAIN
                    verdict = cortex.predict(call_type)
                    
                    # 4. REPORT
                    if "ANOMALY" in verdict:
                        print(f"🔴 BLOCK | {call_type} ({arg_val}) -> {verdict}")
                    else:
                        print(f"🟢 ALLOW | {call_type} ({arg_val}) -> {verdict}")
            except Exception as e:
                print(f"⚠️ Parse Error: {e}")

if __name__ == "__main__":
    try:
        start_listener()
    except KeyboardInterrupt:
        os.unlink(PIPE_PATH)
