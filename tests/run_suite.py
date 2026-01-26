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
    print(f"{YELLOW}[TEST] Building latest binaries...{RESET}")
    subprocess.run(["make"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"{YELLOW}[TEST] Starting Sentinel Neural Engine (Background)...{RESET}")
    # Start the Brain
    brain = subprocess.Popen(
        ["python3", "src/analysis/brain.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(2) # Warmup time for IPC

    print(f"{YELLOW}[TEST] Executing Attack: FD Duplication...{RESET}")
    # Run the Dup Attack
    # We use 'sudo' because Sentinel requires ptrace privileges
    attack = subprocess.run(
        ["sudo", "./bin/sentinel", "test", "./bin/dup_test"],
        capture_output=True,
        text=True
    )

    # Stop the Brain
    brain.terminate()
    try:
        stdout, _ = brain.communicate(timeout=2)
    except:
        brain.kill()
        stdout, _ = brain.communicate()

    # --- VERIFICATION LOGIC ---
    print("-" * 40)

    # Check 1: Did we detect the duplication?
    dup_detected = "Tracking alias" in stdout

    # Check 2: Did we track the write?
    write_tracked = "Sensitive data written to pipe" in stdout

    if dup_detected and write_tracked:
        print(f"{GREEN}[PASS] Evasion Attempt Detected!{RESET}")
        print(f"       Log: 'FD duplicated - Tracking alias'")
        sys.exit(0)
    else:
        print(f"{RED}[FAIL] Attack went unnoticed.{RESET}")
        print("Debug Output from Brain:")
        print(stdout)
        sys.exit(1)

if __name__ == "__main__":
    run_test()