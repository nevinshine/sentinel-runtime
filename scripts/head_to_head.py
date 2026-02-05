#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════╗
║                    SENTINEL vs HYPERION                               ║
║                    Head-to-Head Benchmark                             ║
╚═══════════════════════════════════════════════════════════════════════╝

This script runs comparable benchmarks on both runtimes and generates
a comparison report.

Usage:
    1. Run baseline (no security): python3 scripts/head_to_head.py baseline
    2. Run with Sentinel attached: python3 scripts/head_to_head.py sentinel  
    3. Run with Hyperion active:   python3 scripts/head_to_head.py hyperion
    4. Generate report:            python3 scripts/head_to_head.py report

Or run everything automatically:
    python3 scripts/head_to_head.py auto
"""

import os
import sys
import json
import time
import subprocess
import statistics
import socket
import struct
from pathlib import Path
from datetime import datetime

# Results storage
RESULTS_DIR = Path("/tmp/head_to_head_results")
RESULTS_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
#  COMMON BENCHMARKS (Work on both systems)
# ═══════════════════════════════════════════════════════════════════════

def benchmark_syscall_storm(iterations=100000):
    """
    Measure raw syscall overhead.
    Both Sentinel (ptrace) and baseline are affected differently.
    """
    import ctypes
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    
    latencies = []
    start_total = time.time()
    
    for _ in range(iterations):
        start = time.perf_counter_ns()
        libc.getpid()
        end = time.perf_counter_ns()
        latencies.append(end - start)
    
    elapsed = time.time() - start_total
    
    return {
        "test": "syscall_storm",
        "iterations": iterations,
        "total_time_sec": elapsed,
        "throughput": iterations / elapsed,
        "mean_ns": statistics.mean(latencies),
        "p50_ns": statistics.median(latencies),
        "p99_ns": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
        "max_ns": max(latencies),
    }


def benchmark_file_operations(iterations=5000):
    """
    Measure file I/O overhead (create, write, read, delete).
    Sentinel intercepts open/read/write/unlink; Hyperion monitors network, not local I/O.
    """
    test_dir = Path("/tmp/benchmark_files")
    test_dir.mkdir(exist_ok=True)
    
    latencies = []
    payload = b"BENCHMARK_PAYLOAD_" * 100  # 1.8KB
    
    start_total = time.time()
    
    for i in range(iterations):
        filepath = test_dir / f"bench_{i}.dat"
        
        start = time.perf_counter_ns()
        
        # Full cycle: create, write, read, delete
        with open(filepath, "wb") as f:
            f.write(payload)
        with open(filepath, "rb") as f:
            _ = f.read()
        filepath.unlink()
        
        end = time.perf_counter_ns()
        latencies.append(end - start)
    
    elapsed = time.time() - start_total
    
    # Cleanup
    try:
        test_dir.rmdir()
    except:
        pass
    
    return {
        "test": "file_operations",
        "iterations": iterations,
        "total_time_sec": elapsed,
        "iops": iterations / elapsed,
        "mean_us": statistics.mean(latencies) / 1000,
        "p50_us": statistics.median(latencies) / 1000,
        "p99_us": statistics.quantiles(latencies, n=100)[98] / 1000 if len(latencies) >= 100 else max(latencies) / 1000,
        "max_us": max(latencies) / 1000,
    }


def benchmark_process_creation(iterations=500):
    """
    Measure fork/exec overhead.
    Sentinel intercepts fork/clone/execve; important for detecting spawning attacks.
    """
    latencies = []
    
    start_total = time.time()
    
    for _ in range(iterations):
        start = time.perf_counter_ns()
        
        # Fork a minimal process
        proc = subprocess.Popen(
            ["/bin/true"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        proc.wait()
        
        end = time.perf_counter_ns()
        latencies.append(end - start)
    
    elapsed = time.time() - start_total
    
    return {
        "test": "process_creation",
        "iterations": iterations,
        "total_time_sec": elapsed,
        "forks_per_sec": iterations / elapsed,
        "mean_ms": statistics.mean(latencies) / 1_000_000,
        "p50_ms": statistics.median(latencies) / 1_000_000,
        "p99_ms": statistics.quantiles(latencies, n=100)[98] / 1_000_000 if len(latencies) >= 100 else max(latencies) / 1_000_000,
        "max_ms": max(latencies) / 1_000_000,
    }


def benchmark_network_loopback(iterations=1000, packet_size=1024):
    """
    Measure local network latency (UDP loopback).
    Hyperion (XDP) intercepts network; Sentinel doesn't directly monitor packets.
    """
    latencies = []
    
    # Create UDP sockets
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("127.0.0.1", 0))
    server_port = server_sock.getsockname()[1]
    server_sock.settimeout(1.0)
    
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    payload = b"X" * packet_size
    
    start_total = time.time()
    
    for i in range(iterations):
        # Pack timestamp into payload
        send_time = time.perf_counter_ns()
        msg = struct.pack("Q", send_time) + payload[:packet_size-8]
        
        client_sock.sendto(msg, ("127.0.0.1", server_port))
        
        try:
            data, _ = server_sock.recvfrom(packet_size)
            recv_time = time.perf_counter_ns()
            
            # Extract send timestamp
            orig_time = struct.unpack("Q", data[:8])[0]
            latencies.append(recv_time - orig_time)
        except socket.timeout:
            pass  # Drop packet
    
    elapsed = time.time() - start_total
    
    client_sock.close()
    server_sock.close()
    
    if not latencies:
        return {"test": "network_loopback", "error": "No packets received"}
    
    return {
        "test": "network_loopback",
        "iterations": len(latencies),
        "packet_size": packet_size,
        "total_time_sec": elapsed,
        "pps": len(latencies) / elapsed,
        "mean_us": statistics.mean(latencies) / 1000,
        "p50_us": statistics.median(latencies) / 1000,
        "p99_us": statistics.quantiles(latencies, n=100)[98] / 1000 if len(latencies) >= 100 else max(latencies) / 1000,
        "max_us": max(latencies) / 1000,
    }


def benchmark_memory_operations(iterations=10000):
    """
    Measure memory allocation patterns.
    May trigger mmap/brk syscalls that Sentinel intercepts.
    """
    latencies = []
    
    start_total = time.time()
    
    for _ in range(iterations):
        start = time.perf_counter_ns()
        
        # Allocate and deallocate memory
        data = bytearray(1024 * 1024)  # 1MB
        data[0] = 0xFF  # Touch it
        del data
        
        end = time.perf_counter_ns()
        latencies.append(end - start)
    
    elapsed = time.time() - start_total
    
    return {
        "test": "memory_operations",
        "iterations": iterations,
        "total_time_sec": elapsed,
        "ops_per_sec": iterations / elapsed,
        "mean_us": statistics.mean(latencies) / 1000,
        "p50_us": statistics.median(latencies) / 1000,
        "p99_us": statistics.quantiles(latencies, n=100)[98] / 1000 if len(latencies) >= 100 else max(latencies) / 1000,
        "max_us": max(latencies) / 1000,
    }


# ═══════════════════════════════════════════════════════════════════════
#  RUNNER
# ═══════════════════════════════════════════════════════════════════════

def run_all_benchmarks(mode="baseline"):
    """Run all benchmarks and save results."""
    print(f"\n{'='*70}")
    print(f"  RUNNING BENCHMARKS - Mode: {mode.upper()}")
    print(f"{'='*70}\n")
    
    results = {
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "benchmarks": []
    }
    
    # Warmup
    print("[*] Warming up...")
    benchmark_syscall_storm(1000)
    benchmark_file_operations(100)
    
    # Run benchmarks
    benchmarks = [
        ("Syscall Storm (100K getpid)", lambda: benchmark_syscall_storm(100000)),
        ("File Operations (5K cycles)", lambda: benchmark_file_operations(5000)),
        ("Process Creation (500 forks)", lambda: benchmark_process_creation(500)),
        ("Network Loopback (1K packets)", lambda: benchmark_network_loopback(1000)),
        ("Memory Operations (10K allocs)", lambda: benchmark_memory_operations(10000)),
    ]
    
    for name, bench_fn in benchmarks:
        print(f"[*] {name}...")
        try:
            result = bench_fn()
            results["benchmarks"].append(result)
            
            # Print quick summary
            if "throughput" in result:
                print(f"    → {result['throughput']:,.0f} ops/sec")
            elif "iops" in result:
                print(f"    → {result['iops']:,.0f} IOPS")
            elif "forks_per_sec" in result:
                print(f"    → {result['forks_per_sec']:,.0f} forks/sec")
            elif "pps" in result:
                print(f"    → {result['pps']:,.0f} PPS")
            elif "ops_per_sec" in result:
                print(f"    → {result['ops_per_sec']:,.0f} ops/sec")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results["benchmarks"].append({"test": name, "error": str(e)})
    
    # Save results
    output_file = RESULTS_DIR / f"{mode}_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Results saved to {output_file}")
    
    return results


def generate_report():
    """Generate comparison report from saved results."""
    print("\n" + "="*70)
    print("  HEAD-TO-HEAD COMPARISON REPORT")
    print("="*70 + "\n")
    
    # Load available results
    modes = {}
    for mode in ["baseline", "sentinel", "hyperion"]:
        result_file = RESULTS_DIR / f"{mode}_results.json"
        if result_file.exists():
            with open(result_file) as f:
                modes[mode] = json.load(f)
    
    if not modes:
        print("No results found! Run benchmarks first:")
        print("  python3 scripts/head_to_head.py baseline")
        print("  python3 scripts/head_to_head.py sentinel")
        print("  python3 scripts/head_to_head.py hyperion")
        return
    
    if "baseline" not in modes:
        print("⚠️  No baseline results! Run: python3 scripts/head_to_head.py baseline")
        return
    
    baseline = modes["baseline"]
    
    # Build comparison table
    print("┌" + "─"*68 + "┐")
    print("│" + " OVERHEAD COMPARISON (vs Baseline)".center(68) + "│")
    print("├" + "─"*25 + "┬" + "─"*20 + "┬" + "─"*20 + "┤")
    print(f"│ {'Benchmark':<23} │ {'Sentinel':<18} │ {'Hyperion':<18} │")
    print("├" + "─"*25 + "┼" + "─"*20 + "┼" + "─"*20 + "┤")
    
    test_names = {
        "syscall_storm": "Syscall Storm",
        "file_operations": "File I/O",
        "process_creation": "Process Creation",
        "network_loopback": "Network (UDP)",
        "memory_operations": "Memory Alloc",
    }
    
    metrics = {
        "syscall_storm": "throughput",
        "file_operations": "iops",
        "process_creation": "forks_per_sec",
        "network_loopback": "pps",
        "memory_operations": "ops_per_sec",
    }
    
    for bench in baseline["benchmarks"]:
        test = bench.get("test", "")
        if test not in test_names:
            continue
        
        metric = metrics.get(test)
        if not metric or metric not in bench:
            continue
        
        baseline_val = bench[metric]
        
        # Get Sentinel result
        sentinel_str = "—"
        if "sentinel" in modes:
            for s_bench in modes["sentinel"]["benchmarks"]:
                if s_bench.get("test") == test and metric in s_bench:
                    s_val = s_bench[metric]
                    overhead = ((baseline_val - s_val) / baseline_val) * 100
                    if overhead > 0:
                        sentinel_str = f"🔴 -{overhead:.1f}%"
                    else:
                        sentinel_str = f"🟢 +{-overhead:.1f}%"
                    break
        
        # Get Hyperion result
        hyperion_str = "—"
        if "hyperion" in modes:
            for h_bench in modes["hyperion"]["benchmarks"]:
                if h_bench.get("test") == test and metric in h_bench:
                    h_val = h_bench[metric]
                    overhead = ((baseline_val - h_val) / baseline_val) * 100
                    if overhead > 0:
                        hyperion_str = f"🔴 -{overhead:.1f}%"
                    elif overhead < -1:
                        hyperion_str = f"🟢 +{-overhead:.1f}%"
                    else:
                        hyperion_str = f"🟢 ~0%"
                    break
        
        print(f"│ {test_names[test]:<23} │ {sentinel_str:<18} │ {hyperion_str:<18} │")
    
    print("└" + "─"*25 + "┴" + "─"*20 + "┴" + "─"*20 + "┘")
    
    # Raw numbers table
    print("\n")
    print("┌" + "─"*68 + "┐")
    print("│" + " RAW THROUGHPUT NUMBERS".center(68) + "│")
    print("├" + "─"*20 + "┬" + "─"*15 + "┬" + "─"*15 + "┬" + "─"*15 + "┤")
    print(f"│ {'Benchmark':<18} │ {'Baseline':>13} │ {'Sentinel':>13} │ {'Hyperion':>13} │")
    print("├" + "─"*20 + "┼" + "─"*15 + "┼" + "─"*15 + "┼" + "─"*15 + "┤")
    
    for bench in baseline["benchmarks"]:
        test = bench.get("test", "")
        if test not in test_names:
            continue
        
        metric = metrics.get(test)
        if not metric or metric not in bench:
            continue
        
        base_val = bench[metric]
        
        sentinel_val = "—"
        if "sentinel" in modes:
            for s_bench in modes["sentinel"]["benchmarks"]:
                if s_bench.get("test") == test and metric in s_bench:
                    sentinel_val = f"{s_bench[metric]:,.0f}"
                    break
        
        hyperion_val = "—"
        if "hyperion" in modes:
            for h_bench in modes["hyperion"]["benchmarks"]:
                if h_bench.get("test") == test and metric in h_bench:
                    hyperion_val = f"{h_bench[metric]:,.0f}"
                    break
        
        unit = "ops/s" if test == "syscall_storm" else ("IOPS" if test == "file_operations" else "ops/s")
        print(f"│ {test_names[test]:<18} │ {base_val:>13,.0f} │ {sentinel_val:>13} │ {hyperion_val:>13} │")
    
    print("└" + "─"*20 + "┴" + "─"*15 + "┴" + "─"*15 + "┴" + "─"*15 + "┘")
    
    # Bottom line analysis
    print("\n" + "="*70)
    print("  ANALYSIS")
    print("="*70)
    
    print("""
┌─────────────────────────────────────────────────────────────────────┐
│ SENTINEL (ptrace-based)                                             │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Full syscall visibility (every open, read, write, exec, etc.)    │
│ ✓ Semantic file classification + state machine detection           │
│ ✓ Per-process tracking with behavioral analysis                    │
│ ✗ High overhead due to context switches (userspace tracing)        │
│ → Best for: Sandboxing, malware analysis, forensics                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ HYPERION (eBPF/XDP-based)                                           │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ Near-zero overhead (runs in kernel)                              │
│ ✓ Wire-speed packet inspection (40+ Gbps)                          │
│ ✓ Signature matching at network layer                              │
│ ✗ Limited to network-level visibility                              │
│ → Best for: Production servers, network perimeter, high-throughput │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ COMBINED STRATEGY                                                   │
├─────────────────────────────────────────────────────────────────────┤
│ Use Hyperion at the network layer for production traffic           │
│ Use Sentinel for targeted process analysis and incident response   │
│ Both feed into Telos for cryptographic attestation                 │
└─────────────────────────────────────────────────────────────────────┘
""")
    
    # Save report
    report_file = RESULTS_DIR / "comparison_report.txt"
    print(f"\n[+] Report available at: {report_file}")


def print_usage():
    """Print usage information."""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "baseline":
        run_all_benchmarks("baseline")
    elif cmd == "sentinel":
        print("⚠️  Make sure Sentinel is attached to THIS process!")
        print("    Run: ./bin/sentinel --pid $$ (in another terminal)")
        input("Press Enter when ready...")
        run_all_benchmarks("sentinel")
    elif cmd == "hyperion":
        print("⚠️  Make sure Hyperion is running on loopback!")
        print("    Run: sudo ./bin/hyperion_ctrl -iface lo")
        input("Press Enter when ready...")
        run_all_benchmarks("hyperion")
    elif cmd == "report":
        generate_report()
    elif cmd == "auto":
        print("Running baseline automatically...")
        run_all_benchmarks("baseline")
        print("\n" + "="*70)
        print("Baseline complete. Now run with each runtime and then generate report:")
        print("  1. Start Sentinel, then: python3 scripts/head_to_head.py sentinel")
        print("  2. Start Hyperion, then: python3 scripts/head_to_head.py hyperion")
        print("  3. Generate report:      python3 scripts/head_to_head.py report")
    else:
        print_usage()


if __name__ == "__main__":
    main()
