import os

REQ = "/tmp/sentinel_req"
RESP = "/tmp/sentinel_resp"

# Ensure pipes exist
if not os.path.exists(REQ): os.mkfifo(REQ)
if not os.path.exists(RESP): os.mkfifo(RESP)

print("🧠 Mock Brain V2: Initialization...")

# 1. OPEN BOTH PIPES BEFORE READING (Fixes the C Deadlock)
# We open REQ for reading and RESP for writing immediately.
print("   [1/2] Connecting to Request Channel...")
f_req = open(REQ, "r") 
print("   [2/2] Connecting to Response Channel...")
f_resp = open(RESP, "w") 

# Make buffers unbuffered for speed
# (Python 3 open() defaults to buffered, so we flush manually below)

print("✅ LINK ESTABLISHED. Waiting for malware...")

while True:
    # 2. Read Request
    data = f_req.readline()
    if not data: break # Pipe broken
    
    cmd = data.strip()
    print(f"   [ANALYSIS] Received: {cmd}")
    
    # 3. Decision Logic (Block 'RANSOMWARE')
    verdict = "0" if "RANSOM" in cmd else "1"
    
    # 4. Send Response
    f_resp.write(verdict)
    f_resp.flush() # Force send immediately
    print(f"   [DECISION] Sent: {'BLOCK' if verdict=='0' else 'ALLOW'}")

# Cleanup
f_req.close()
f_resp.close()
