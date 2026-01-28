import subprocess
import time
import sys
import os

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def run_test():
    # 0. Sudo Refresh: Ensure we have permissions before starting
    subprocess.run(["sudo", "-v"], check=False)

    print(f"{YELLOW}[TEST] Building latest binaries...{RESET}")
    subprocess.run(["make"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"{YELLOW}[TEST] Starting Sentinel Neural Engine (Background)...{RESET}")

    # FIX 1: Use '-u' to force UNBUFFERED output so logs aren't lost
    brain = subprocess.Popen(
        ["python3", "-u", "src/analysis/brain.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # Capture everything
        text=True
    )
    time.sleep(2) # Warmup time for IPC

    print(f"{YELLOW}[TEST] Executing Attack: FD Duplication...{RESET}")
    # Run the Dup Attack
    subprocess.run(
        ["sudo", "./bin/sentinel", "test", "./bin/dup_test"],
        capture_output=True,
        text=True
    )

    # Stop the Brain gracefully
    brain.terminate()
    try:
        stdout, _ = brain.communicate(timeout=2)
    except:
        brain.kill()
        stdout, _ = brain.communicate()

    # --- VERIFICATION LOGIC ---
    print("-" * 40)

    # Check 1: Did we detect the duplication?
    # (Matches the 'print("... Status: Tracking alias")' you added to brain.py)
    dup_detected = "Tracking alias" in stdout

    # FIX 2: Check for the ACTUAL string your brain.py prints
    # Your brain prints "EXFILTRATION ATTEMPT BLOCKED", not "data written to pipe"
    write_tracked = "EXFILTRATION ATTEMPT BLOCKED" in stdout

    if dup_detected and write_tracked:
        print(f"{GREEN}[PASS] Evasion Attempt Detected!{RESET}")
        print(f"       Log: 'FD duplicated - Tracking alias'")
        sys.exit(0)
    else:
        print(f"{RED}[FAIL] Attack went unnoticed or Logs were lost.{RESET}")
        print("Debug Output from Brain:")
        print(stdout)
        sys.exit(1)

if __name__ == "__main__":
    run_test()