import os
import sys

# IPC Configuration
REQ_PIPE = os.environ.get("SENTINEL_PIPE_REQ", "/tmp/sentinel_req")
RESP_PIPE = os.environ.get("SENTINEL_PIPE_RESP", "/tmp/sentinel_resp")

def ensure_pipes():
    if not os.path.exists(REQ_PIPE):
        os.mkfifo(REQ_PIPE)
    if not os.path.exists(RESP_PIPE):
        os.mkfifo(RESP_PIPE)

def main():
    print("[INFO] Initializing Sentinel Logic Engine...")
    
    ensure_pipes()

    # Open pipes: Request (Read) and Response (Write)
    # Opening order is critical to prevent race conditions with the C client
    print("[INFO] Connecting to Request Channel...")
    f_req = open(REQ_PIPE, "r")
    
    print("[INFO] Connecting to Response Channel...")
    f_resp = open(RESP_PIPE, "w")

    print("[INFO] System Active. Monitoring syscall stream...")

    while True:
        # 1. Read Syscall Event
        raw_data = f_req.readline()
        if not raw_data:
            break  # Pipe closed or EOF
        
        cmd = raw_data.strip()
        
        # 2. Decision Logic
        # Policy: Block any attempt to delete files or directories
        # Syscalls: unlink (delete file), rmdir (delete directory)
        if "unlink" in cmd or "rmdir" in cmd:
            verdict = "0" # Block
            log_status = "BLOCKED"
        else:
            verdict = "1" # Allow
            log_status = "ALLOWED"

        # 3. Transmit Verdict
        f_resp.write(verdict)
        f_resp.flush() # Ensure immediate transmission to kernel hook

        # 4. Log Analysis
        if verdict == "0":
            print(f"[ALERT] {log_status}: {cmd}")
        else:
            print(f"[LOG]   {log_status}: {cmd}")

    # Cleanup
    f_req.close()
    f_resp.close()
    print("[INFO] Session Terminated.")

if __name__ == "__main__":
    main()
