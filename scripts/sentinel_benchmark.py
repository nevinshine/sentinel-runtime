#!/usr/bin/env python3
"""
Sentinel Benchmark Script - Collect REAL performance data
==========================================================
Run this script to measure actual Sentinel Brain latency.

Usage:
    1. Copy to sentinel-runtime/scripts/benchmark.py
    2. Run: python3 scripts/benchmark.py

This will output measurements you can add to the dossier benchmarks doc.
"""

import os
import sys
import time
import json
import statistics

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'analysis'))

try:
    from semantic import SemanticMapper
    from state_machine import ExfiltrationDetector
except ImportError:
    print("[!] Run this from sentinel-runtime root: python3 scripts/benchmark.py")
    sys.exit(1)


def benchmark_semantic_mapper(iterations=1000):
    """Measure SemanticMapper.classify() latency."""
    mapper = SemanticMapper()
    
    test_paths = [
        "/etc/passwd",
        "/home/user/.ssh/id_rsa",
        "/usr/lib/libcrypto.so",
        "/tmp/malware.exe",
        "/proc/self/maps",
        "/home/user/Documents/secret.pdf",
        "/var/log/syslog",
        "/dev/null",
    ]
    
    latencies = []
    
    for _ in range(iterations):
        for path in test_paths:
            start = time.perf_counter_ns()
            _ = mapper.classify(path)
            end = time.perf_counter_ns()
            latencies.append(end - start)
    
    return latencies


def benchmark_state_machine(iterations=1000):
    """Measure ExfiltrationDetector.process_event() latency."""
    detector = ExfiltrationDetector()
    
    # Simulate realistic event sequence
    events = [
        (1234, "open", {"fd": "3", "ret": "0"}, "SENSITIVE_USER_FILE"),
        (1234, "read", {"fd": "3", "ret": "4096"}, ""),
        (1234, "socket", {"fd": "5", "ret": "5"}, ""),
        (1234, "connect", {"fd": "5", "ret": "0"}, ""),
        (1234, "sendto", {"fd": "5", "ret": "1024"}, ""),
    ]
    
    latencies = []
    
    for _ in range(iterations):
        for pid, verb, args, concept in events:
            start = time.perf_counter_ns()
            _ = detector.process_event(pid, verb, args, concept)
            end = time.perf_counter_ns()
            latencies.append(end - start)
    
    return latencies


def benchmark_full_decision(iterations=500):
    """Measure full decision loop (semantic + state machine)."""
    mapper = SemanticMapper()
    detector = ExfiltrationDetector()
    
    test_events = [
        ("open", "/home/user/.ssh/id_rsa", 1234),
        ("read", "", 1234),
        ("socket", "", 1234),
        ("connect", "192.168.1.1", 1234),
        ("sendto", "", 1234),
        ("unlink", "/tmp/test.txt", 5678),
        ("execve", "/usr/bin/bash", 9999),
    ]
    
    latencies = []
    
    for _ in range(iterations):
        for verb, path, pid in test_events:
            start = time.perf_counter_ns()
            
            # Semantic classification
            concept = mapper.classify(path) if path else "N/A"
            
            # State machine
            args = {"fd": "3", "ret": "0"}
            verdict = detector.process_event(pid, verb, args, concept)
            
            end = time.perf_counter_ns()
            latencies.append(end - start)
    
    return latencies


def print_stats(name, latencies_ns):
    """Print statistics for a benchmark."""
    latencies_us = [l / 1000 for l in latencies_ns]  # Convert to μs
    
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Samples:    {len(latencies_us)}")
    print(f"  Mean:       {statistics.mean(latencies_us):.2f} μs")
    print(f"  Median:     {statistics.median(latencies_us):.2f} μs")
    print(f"  Std Dev:    {statistics.stdev(latencies_us):.2f} μs")
    print(f"  Min:        {min(latencies_us):.2f} μs")
    print(f"  Max:        {max(latencies_us):.2f} μs")
    print(f"  P95:        {statistics.quantiles(latencies_us, n=20)[18]:.2f} μs")
    print(f"  P99:        {statistics.quantiles(latencies_us, n=100)[98]:.2f} μs")
    
    return {
        "name": name,
        "mean_us": statistics.mean(latencies_us),
        "median_us": statistics.median(latencies_us),
        "p95_us": statistics.quantiles(latencies_us, n=20)[18],
        "p99_us": statistics.quantiles(latencies_us, n=100)[98],
    }


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           SENTINEL BENCHMARK SUITE                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    results = []
    
    # Warmup
    print("[*] Warming up...")
    benchmark_semantic_mapper(100)
    benchmark_state_machine(100)
    
    # Actual benchmarks
    print("[*] Running SemanticMapper benchmark (1000 iterations)...")
    semantic_latencies = benchmark_semantic_mapper(1000)
    results.append(print_stats("SemanticMapper.classify()", semantic_latencies))
    
    print("\n[*] Running ExfiltrationDetector benchmark (1000 iterations)...")
    state_latencies = benchmark_state_machine(1000)
    results.append(print_stats("ExfiltrationDetector.process_event()", state_latencies))
    
    print("\n[*] Running Full Decision Loop benchmark (500 iterations)...")
    full_latencies = benchmark_full_decision(500)
    results.append(print_stats("Full Decision Loop (semantic + state)", full_latencies))
    
    # Summary for dossier
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           COPY TO DOSSIER benchmarks.md                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("| Metric | Mean | P95 | P99 | Status |")
    print("|--------|------|-----|-----|--------|")
    for r in results:
        print(f"| **{r['name'][:40]}** | {r['mean_us']:.1f} μs | {r['p95_us']:.1f} μs | {r['p99_us']:.1f} μs | 🟢 MEASURED |")
    
    # Save JSON
    with open("sentinel_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Results saved to sentinel_benchmark_results.json")


if __name__ == "__main__":
    main()
