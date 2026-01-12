# analysis/bridge.py
import os
import time

PIPE_PATH = "/tmp/sentinel_ipc"

def start_listener():
    # 1. Create the Named Pipe (FIFO) if it doesn't exist
    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)
    
    print(f"[BRIDGE] 👂 Listening on {PIPE_PATH}...")

    # 2. Open the pipe like a normal file
    # We open in "r" (Read) mode. 
    # This will BLOCK (wait) until the C program opens it for writing.
    with open(PIPE_PATH, "r") as pipe:
        while True:
            # 3. Read line by line from the C engine
            line = pipe.readline()
            
            if not line: 
                # If C engine closes, we wait or break
                break 
                
            # 4. Process the data (Just print for now)
            print(f"[BRAIN] 🧠 Received: {line.strip()}")

if __name__ == "__main__":
    try:
        start_listener()
    except KeyboardInterrupt:
        print("\n[BRIDGE] Closing connection.")
        os.unlink(PIPE_PATH) # Cleanup the file
