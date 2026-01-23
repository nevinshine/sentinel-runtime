#!/usr/bin/env python3
"""
Benchmark: Memory Profile
Tracks RAM usage of Sentinel components.

Usage:
    # Run while Sentinel is active
    python3 benchmarks/memory_profile.py
"""

import os
import sys
import time
import subprocess

def get_process_memory(pid):
    """Get memory usage of a process in KB."""
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except:
        return 0
    return 0

def get_process_by_name(name):
    """Find PID by process name."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", name],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split("\n")
        return [int(p) for p in pids if p]
    except:
        return []

def monitor_memory(duration=30, interval=1.0):
    """Monitor memory usage over time."""
    print(f"\n[*] Monitoring memory for {duration} seconds...")
    print(f"    Interval: {interval}s\n")

    samples = {
        "sentinel": [],
        "brain": [],
        "total": []
    }

    print(f"{'Time (s)':<10} {'Sentinel (KB)':<15} {'Brain (KB)':<15} {'Total (KB)':<15}")
    print("-" * 55)

    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time

        # Find processes
        sentinel_pids = get_process_by_name("bin/sentinel")
        brain_pids = get_process_by_name("brain.py")

        sentinel_mem = sum(get_process_memory(p) for p in sentinel_pids)
        brain_mem = sum(get_process_memory(p) for p in brain_pids)
        total_mem = sentinel_mem + brain_mem

        samples["sentinel"].append(sentinel_mem)
        samples["brain"].append(brain_mem)
        samples["total"].append(total_mem)

        print(f"{elapsed:<10.1f} {sentinel_mem:<15,} {brain_mem:<15,} {total_mem:<15,}")

        time.sleep(interval)

    # Summary
    print(f"\n{'='*60}")
    print(f"  MEMORY SUMMARY")
    print(f"{'='*60}")

    for name, data in samples.items():
        if data and max(data) > 0:
            print(f"\n  {name.upper()}:")
            print(f"    Min:  {min(data):,} KB ({min(data)/1024:.1f} MB)")
            print(f"    Max:  {max(data):,} KB ({max(data)/1024:.1f} MB)")
            print(f"    Avg:  {sum(data)//len(data):,} KB ({sum(data)/len(data)/1024:.1f} MB)")

def main():
    print(f"\n{'#'*60}")
    print(f"  SENTINEL MEMORY PROFILE BENCHMARK")
    print(f"{'#'*60}")

    # Check if Sentinel is running
    sentinel_pids = get_process_by_name("bin/sentinel")
    brain_pids = get_process_by_name("brain.py")

    if not sentinel_pids and not brain_pids:
        print("\n[!] No Sentinel processes found.")
        print("    Start Sentinel first:")
        print("      Terminal 1: cd src/analysis && python3 brain.py")
        print("      Terminal 2: sudo ./bin/sentinel test /bin/bash")
        print("\n    Then run this benchmark in a third terminal.")
        sys.exit(1)

    print(f"\n[*] Found Sentinel PIDs: {sentinel_pids}")
    print(f"[*] Found Brain PIDs: {brain_pids}")

    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    monitor_memory(duration=duration)

if __name__ == "__main__":
    main()