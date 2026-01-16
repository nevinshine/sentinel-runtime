# analysis/bridge.py
import os
import time
from brain import WiSARD

PIPE_REQ = "/tmp/sentinel_req"
PIPE_RESP = "/tmp/sentinel_resp"

def start_listener():
    cortex = WiSARD()
    # Ensure pipes exist
    if not os.path.exists(PIPE_REQ): os.mkfifo(PIPE_REQ)
    if not os.path.exists(PIPE_RESP): os.mkfifo(PIPE_RESP)

    print("[BRIDGE] 👁️  Semantic Analysis Online.")

    while True:
        with open(PIPE_REQ, "r") as req_pipe, open(PIPE_RESP, "w") as resp_pipe:
            while True:
                line = req_pipe.readline()
                if not line: break
                
                try:
                    parts = line.strip().split(":")
                    if len(parts) >= 3:
                        syscall = parts[1] # "mkdir"
                        arg = parts[2]     # "/path/to/folder"
                        
                        # --- SEMANTIC POLICY ---
                        # Rule: "malware" folders are forbidden.
                        if "malware" in arg:
                            print(f"🔴 BLOCK | {syscall} ('{arg}') -> 🚨 MALICIOUS INTENT")
                            resp_pipe.write("0\n") 
                        else:
                            print(f"🟢 ALLOW | {syscall} ('{arg}') -> ✅ SAFE")
                            resp_pipe.write("1\n")
                            
                        resp_pipe.flush()
                except Exception as e:
                    print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    start_listener()
