#!/usr/bin/env python3
"""
Sentinel STRESS TEST - Push the Brain to its limits
====================================================
This is the BRUTAL benchmark. We're testing:
1. High-frequency burst events (10K/sec simulation)
2. Adversarial path patterns (edge cases)
3. State explosion (many concurrent PIDs)
4. Memory pressure under sustained load
5. Worst-case attack chain detection

Usage:
    1. Copy to sentinel-runtime/scripts/stress_test.py
    2. Run: python3 scripts/stress_test.py

WARNING: This will stress your CPU for ~30 seconds.
"""

import os
import sys
import time
import json
import random
import string
import statistics
import gc
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'analysis'))

try:
    from semantic import SemanticMapper
    from state_machine import ExfiltrationDetector
except ImportError:
    print("[!] Run this from sentinel-runtime root: python3 scripts/stress_test.py")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
#  ADVERSARIAL PATH PATTERNS
# ═══════════════════════════════════════════════════════════════

ADVERSARIAL_PATHS = [
    # Deeply nested paths (directory traversal attempts)
    "/".join(["a" * 10] * 50),
    "/home/user/../../../etc/passwd",
    "/home/user/.ssh/../.ssh/../.ssh/id_rsa",
    
    # Unicode madness
    "/home/user/документы/секретный.pdf",
    "/home/用户/文档/机密.docx",
    "/tmp/\x00\x01\x02malicious",
    
    # Path length edge cases
    "/" + "x" * 4095,  # Near PATH_MAX
    "",  # Empty path
    ".",
    "..",
    
    # Special filesystem paths
    "/proc/self/mem",
    "/proc/self/exe",
    "/dev/mem",
    "/dev/kmem",
    "/sys/kernel/security/whatever",
    
    # Hidden file variations
    "/home/user/.hidden/.nested/.deep/secret",
    "/home/user/....",
    "/home/user/. ",
    
    # Container escape attempts
    "/var/run/docker.sock",
    "/run/containerd/containerd.sock",
    "/proc/1/root/etc/passwd",
    
    # High-value targets
    "/etc/shadow",
    "/root/.bash_history",
    "/var/log/auth.log",
    "/home/user/.aws/credentials",
    "/home/user/.kube/config",
    "/home/user/.gnupg/secring.gpg",
]


# ═══════════════════════════════════════════════════════════════
#  TEST 1: BURST EVENT STORM
# ═══════════════════════════════════════════════════════════════

def test_burst_event_storm(duration_sec=5):
    """Simulate a burst of events at maximum speed."""
    print("\n[TEST 1] BURST EVENT STORM")
    print("-" * 60)
    
    mapper = SemanticMapper()
    detector = ExfiltrationDetector()
    
    events_processed = 0
    latencies = []
    
    verbs = ["open", "read", "write", "close", "socket", "connect", "sendto", "recvfrom"]
    paths = ["/etc/passwd", "/home/user/.ssh/id_rsa", "/tmp/test", "/dev/null"]
    
    start_time = time.time()
    deadline = start_time + duration_sec
    
    while time.time() < deadline:
        pid = random.randint(1000, 9999)
        verb = random.choice(verbs)
        path = random.choice(paths)
        
        event_start = time.perf_counter_ns()
        
        concept = mapper.classify(path)
        detector.process_event(pid, verb, {"fd": "3", "ret": "0"}, concept)
        
        event_end = time.perf_counter_ns()
        latencies.append(event_end - event_start)
        events_processed += 1
    
    elapsed = time.time() - start_time
    throughput = events_processed / elapsed
    latencies_us = [l / 1000 for l in latencies]
    
    print(f"  Duration:      {elapsed:.2f}s")
    print(f"  Events:        {events_processed:,}")
    print(f"  Throughput:    {throughput:,.0f} events/sec")
    print(f"  Mean latency:  {statistics.mean(latencies_us):.2f} μs")
    print(f"  P99 latency:   {statistics.quantiles(latencies_us, n=100)[98]:.2f} μs")
    print(f"  Max latency:   {max(latencies_us):.2f} μs")
    
    return {
        "test": "burst_event_storm",
        "throughput": throughput,
        "mean_us": statistics.mean(latencies_us),
        "p99_us": statistics.quantiles(latencies_us, n=100)[98],
        "max_us": max(latencies_us),
    }


# ═══════════════════════════════════════════════════════════════
#  TEST 2: ADVERSARIAL PATH FUZZING
# ═══════════════════════════════════════════════════════════════

def test_adversarial_paths(iterations=1000):
    """Test with adversarial/edge case paths."""
    print("\n[TEST 2] ADVERSARIAL PATH FUZZING")
    print("-" * 60)
    
    mapper = SemanticMapper()
    
    latencies = []
    errors = 0
    
    for _ in range(iterations):
        for path in ADVERSARIAL_PATHS:
            try:
                start = time.perf_counter_ns()
                _ = mapper.classify(path)
                end = time.perf_counter_ns()
                latencies.append(end - start)
            except Exception as e:
                errors += 1
    
    latencies_us = [l / 1000 for l in latencies]
    
    print(f"  Samples:       {len(latencies):,}")
    print(f"  Errors:        {errors}")
    print(f"  Mean latency:  {statistics.mean(latencies_us):.2f} μs")
    print(f"  P99 latency:   {statistics.quantiles(latencies_us, n=100)[98]:.2f} μs")
    print(f"  Max latency:   {max(latencies_us):.2f} μs")
    
    return {
        "test": "adversarial_paths",
        "samples": len(latencies),
        "errors": errors,
        "mean_us": statistics.mean(latencies_us),
        "p99_us": statistics.quantiles(latencies_us, n=100)[98],
        "max_us": max(latencies_us),
    }


# ═══════════════════════════════════════════════════════════════
#  TEST 3: STATE EXPLOSION (Many Concurrent PIDs)
# ═══════════════════════════════════════════════════════════════

def test_state_explosion(num_pids=1000, events_per_pid=20):
    """Create many concurrent process states."""
    print("\n[TEST 3] STATE EXPLOSION ({} concurrent PIDs)".format(num_pids))
    print("-" * 60)
    
    mapper = SemanticMapper()
    detector = ExfiltrationDetector()
    
    # Generate PIDs
    pids = list(range(10000, 10000 + num_pids))
    
    # Event sequence for each PID
    event_sequence = [
        ("open", "/home/user/secret.txt", "SENSITIVE_USER_FILE"),
        ("read", "", ""),
        ("socket", "", ""),
        ("connect", "192.168.1.1", ""),
        ("sendto", "", ""),
    ]
    
    latencies = []
    alerts_triggered = 0
    
    start_time = time.time()
    
    # Round-robin events across all PIDs
    for event_idx in range(events_per_pid):
        for pid in pids:
            if event_idx < len(event_sequence):
                verb, path, concept = event_sequence[event_idx % len(event_sequence)]
            else:
                verb, path, concept = "read", "", ""
            
            event_start = time.perf_counter_ns()
            result = detector.process_event(pid, verb, {"fd": "3", "ret": "0"}, concept)
            event_end = time.perf_counter_ns()
            
            latencies.append(event_end - event_start)
            if result and result.alert:
                alerts_triggered += 1
    
    elapsed = time.time() - start_time
    latencies_us = [l / 1000 for l in latencies]
    
    print(f"  Total events:  {len(latencies):,}")
    print(f"  Elapsed:       {elapsed:.2f}s")
    print(f"  Alerts:        {alerts_triggered}")
    print(f"  Mean latency:  {statistics.mean(latencies_us):.2f} μs")
    print(f"  P99 latency:   {statistics.quantiles(latencies_us, n=100)[98]:.2f} μs")
    print(f"  Max latency:   {max(latencies_us):.2f} μs")
    
    # Check memory growth
    import tracemalloc
    tracemalloc.start()
    
    # Run again to measure memory
    for pid in pids[:100]:
        for verb, path, concept in event_sequence:
            detector.process_event(pid, verb, {"fd": "3", "ret": "0"}, concept)
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"  Memory (peak): {peak / 1024:.1f} KB")
    
    return {
        "test": "state_explosion",
        "num_pids": num_pids,
        "events": len(latencies),
        "alerts": alerts_triggered,
        "mean_us": statistics.mean(latencies_us),
        "p99_us": statistics.quantiles(latencies_us, n=100)[98],
        "max_us": max(latencies_us),
        "memory_peak_kb": peak / 1024,
    }


# ═══════════════════════════════════════════════════════════════
#  TEST 4: ATTACK CHAIN GAUNTLET
# ═══════════════════════════════════════════════════════════════

def test_attack_chain_gauntlet(iterations=100):
    """Test detection of various attack chains."""
    print("\n[TEST 4] ATTACK CHAIN GAUNTLET")
    print("-" * 60)
    
    mapper = SemanticMapper()
    detector = ExfiltrationDetector()
    
    # Different attack patterns to test
    attack_chains = [
        # Classic exfiltration
        [
            ("open", "/home/user/.ssh/id_rsa", "SENSITIVE_USER_FILE"),
            ("read", "", ""),
            ("socket", "", ""),
            ("connect", "", ""),
            ("sendto", "", ""),
        ],
        # Credential theft
        [
            ("open", "/etc/shadow", "SYSTEM_SECURITY_FILE"),
            ("read", "", ""),
            ("write", "/tmp/.cache", ""),
            ("execve", "/usr/bin/curl", ""),
        ],
        # Ransomware pattern
        [
            ("open", "/home/user/Documents/important.docx", "SENSITIVE_USER_FILE"),
            ("read", "", ""),
            ("open", "/home/user/Documents/important.docx.encrypted", ""),
            ("write", "", ""),
            ("unlink", "/home/user/Documents/important.docx", ""),
        ],
        # Reverse shell
        [
            ("socket", "", ""),
            ("connect", "", ""),
            ("dup2", "", ""),
            ("dup2", "", ""),
            ("execve", "/bin/bash", ""),
        ],
        # Log tampering
        [
            ("open", "/var/log/auth.log", "SYSTEM_LOG_FILE"),
            ("write", "", ""),
            ("unlink", "/var/log/wtmp", ""),
        ],
    ]
    
    results = defaultdict(lambda: {"detected": 0, "missed": 0})
    latencies = []
    
    for _ in range(iterations):
        for chain_idx, chain in enumerate(attack_chains):
            chain_name = ["exfil", "cred_theft", "ransomware", "revshell", "log_tamper"][chain_idx]
            pid = random.randint(1000, 9999)
            detected = False
            
            for verb, path, concept in chain:
                if not concept and path:
                    concept = mapper.classify(path)
                
                start = time.perf_counter_ns()
                result = detector.process_event(pid, verb, {"fd": "3", "ret": "0"}, concept)
                end = time.perf_counter_ns()
                latencies.append(end - start)
                
                if result and result.alert:
                    detected = True
            
            if detected:
                results[chain_name]["detected"] += 1
            else:
                results[chain_name]["missed"] += 1
    
    latencies_us = [l / 1000 for l in latencies]
    
    print(f"  Attack patterns tested: {len(attack_chains)}")
    print(f"  Iterations per pattern: {iterations}")
    print(f"  Mean latency:  {statistics.mean(latencies_us):.2f} μs")
    print()
    print("  Detection rates:")
    for chain_name, stats in results.items():
        total = stats["detected"] + stats["missed"]
        rate = (stats["detected"] / total * 100) if total > 0 else 0
        status = "✅" if rate > 80 else "⚠️" if rate > 50 else "❌"
        print(f"    {status} {chain_name}: {rate:.0f}% ({stats['detected']}/{total})")
    
    return {
        "test": "attack_chain_gauntlet",
        "mean_us": statistics.mean(latencies_us),
        "p99_us": statistics.quantiles(latencies_us, n=100)[98],
        "detection_results": dict(results),
    }


# ═══════════════════════════════════════════════════════════════
#  TEST 5: SUSTAINED LOAD (Memory Pressure)
# ═══════════════════════════════════════════════════════════════

def test_sustained_load(duration_sec=10):
    """Sustained load to check for memory leaks and degradation."""
    print("\n[TEST 5] SUSTAINED LOAD ({} seconds)".format(duration_sec))
    print("-" * 60)
    
    import tracemalloc
    tracemalloc.start()
    
    mapper = SemanticMapper()
    detector = ExfiltrationDetector()
    
    # Sample latencies at intervals
    interval_stats = []
    interval_duration = 1.0  # 1 second intervals
    
    overall_start = time.time()
    interval_start = time.time()
    interval_latencies = []
    
    events_total = 0
    
    while time.time() - overall_start < duration_sec:
        pid = random.randint(1000, 99999)
        path = random.choice(["/etc/passwd", "/home/user/.ssh/id_rsa", "/tmp/test"])
        verb = random.choice(["open", "read", "socket", "connect", "sendto"])
        
        start = time.perf_counter_ns()
        concept = mapper.classify(path)
        detector.process_event(pid, verb, {"fd": "3", "ret": "0"}, concept)
        end = time.perf_counter_ns()
        
        interval_latencies.append((end - start) / 1000)  # μs
        events_total += 1
        
        # Check if interval complete
        if time.time() - interval_start >= interval_duration:
            current_mem, _ = tracemalloc.get_traced_memory()
            interval_stats.append({
                "second": len(interval_stats) + 1,
                "events": len(interval_latencies),
                "mean_us": statistics.mean(interval_latencies),
                "p99_us": statistics.quantiles(interval_latencies, n=100)[98] if len(interval_latencies) >= 100 else max(interval_latencies),
                "memory_kb": current_mem / 1024,
            })
            interval_latencies = []
            interval_start = time.time()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Check for degradation
    if len(interval_stats) >= 2:
        first_half_mean = statistics.mean([s["mean_us"] for s in interval_stats[:len(interval_stats)//2]])
        second_half_mean = statistics.mean([s["mean_us"] for s in interval_stats[len(interval_stats)//2:]])
        degradation = ((second_half_mean - first_half_mean) / first_half_mean) * 100
    else:
        degradation = 0
    
    print(f"  Total events:  {events_total:,}")
    print(f"  Memory (peak): {peak / 1024:.1f} KB")
    print(f"  Memory (end):  {current / 1024:.1f} KB")
    print()
    print("  Timeline:")
    for stat in interval_stats:
        mem_bar = "█" * int(stat["memory_kb"] / 10)
        print(f"    [sec {stat['second']:2d}] {stat['events']:,} events, mean={stat['mean_us']:.1f}μs, mem={stat['memory_kb']:.0f}KB {mem_bar}")
    
    print()
    if degradation > 10:
        print(f"  ⚠️  Latency degradation: {degradation:.1f}% (investigate!)")
    else:
        print(f"  ✅ No significant degradation: {degradation:.1f}%")
    
    return {
        "test": "sustained_load",
        "duration_sec": duration_sec,
        "total_events": events_total,
        "memory_peak_kb": peak / 1024,
        "memory_final_kb": current / 1024,
        "degradation_pct": degradation,
        "timeline": interval_stats,
    }


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     🔥 SENTINEL STRESS TEST - BRUTAL MODE 🔥                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("This will push the Sentinel Brain to its absolute limits.")
    print("Estimated runtime: ~30 seconds")
    print()
    
    # Force GC before starting
    gc.collect()
    
    results = []
    
    # Run all tests
    results.append(test_burst_event_storm(duration_sec=5))
    gc.collect()
    
    results.append(test_adversarial_paths(iterations=500))
    gc.collect()
    
    results.append(test_state_explosion(num_pids=1000, events_per_pid=20))
    gc.collect()
    
    results.append(test_attack_chain_gauntlet(iterations=100))
    gc.collect()
    
    results.append(test_sustained_load(duration_sec=10))
    
    # Final summary
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    STRESS TEST SUMMARY                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("| Test | Mean | P99 | Max | Verdict |")
    print("|------|------|-----|-----|---------|")
    for r in results:
        if "mean_us" in r:
            mean = r.get("mean_us", 0)
            p99 = r.get("p99_us", 0)
            max_lat = r.get("max_us", 0)
            
            # Verdict based on P99
            if p99 < 5:
                verdict = "🟢 EXCELLENT"
            elif p99 < 20:
                verdict = "🟡 GOOD"
            else:
                verdict = "🔴 SLOW"
            
            print(f"| {r['test'][:25]:<25} | {mean:.1f} μs | {p99:.1f} μs | {max_lat:.1f} μs | {verdict} |")
    
    # Save results
    with open("sentinel_stress_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[+] Results saved to sentinel_stress_results.json")
    
    # Overall verdict
    print()
    avg_p99 = statistics.mean([r.get("p99_us", 0) for r in results if "p99_us" in r])
    if avg_p99 < 5:
        print("🏆 VERDICT: Sentinel Brain is BLAZING FAST! Sub-5μs P99 under stress!")
    elif avg_p99 < 20:
        print("✅ VERDICT: Sentinel Brain performs well under stress.")
    else:
        print("⚠️  VERDICT: Performance degrades under stress. Investigation needed.")


if __name__ == "__main__":
    main()
