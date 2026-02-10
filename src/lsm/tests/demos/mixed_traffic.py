import os
import time
import subprocess
import random
import sys

# Define commands
NORMAL_CMDS = ["date", "whoami", "pwd", "ls -1", "echo ALIVE", "sleep 0.1"]
ATTACK_CMDS = ["ping -c 1 8.8.8.8", "ping -c 1 1.1.1.1"] # Should be BLOCKED by Sentinel

PID = os.getpid()
print(f"[*] Mixed Traffic Generator (PID {PID})")
print(f"[*] Generating Normal (90%) + Blocked (10%) traffic...")
print(f"[*] IMPORTANT: Run 'sudo ./sentinel_loader mark {PID}' in another terminal to track me!")

try:
    while True:
        # 10% chance of attack (Blocked Command)
        if random.random() < 0.1:
            cmd = random.choice(ATTACK_CMDS)
            print(f"[!] SIMULATING ATTACK: {cmd}")
            # We quell output so we don't spam terminal with permission denied errors too much
            subprocess.call(cmd, shell=True, stderr=subprocess.DEVNULL) 
        else:
            # 90% chance of normal behavior (Allowed Command)
            cmd = random.choice(NORMAL_CMDS)
            # print(f"[.] Normal Activity: {cmd}") 
            subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)
        
        # Random sleep to vary load (0.1s to 0.5s)
        time.sleep(random.uniform(0.1, 0.5))

except KeyboardInterrupt:
    print("\nExiting...")
