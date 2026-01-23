#!/usr/bin/env python3
"""
Benchmark: Syscall Latency
Measures the overhead of Sentinel's ptrace interception per syscall.

Usage:
    # Native (baseline)
    python3 benchmarks/syscall_latency.py native

    # With Sentinel tracing
    sudo ./bin/sentinel test python3 benchmarks/syscall_latency.py traced
"""

import os
import sys
import time
import statistics

# Number of iterations for accurate measurement
ITERATIONS = 10000

def benchmark_open_close():
    """Benchmark open/close syscall pair."""
    times = []
    test_file = "/tmp/sentinel_bench_test"

    # Warmup
    for _ in range(100):
        fd = os.open(test_file, os.O_CREAT | os.O_WRONLY, 0o644)
        os.close(fd)

    # Actual benchmark
    for _ in range(ITERATIONS):
        start = time.perf_counter_ns()
        fd = os.open(test_file, os.O_CREAT | os.O_WRONLY, 0o644)
        os.close(fd)
        end = time.perf_counter_ns()
        times.append(end - start)

    os.unlink(test_file)
    return times

def benchmark_read():
    """Benchmark read syscall."""
    times = []

    # Create test file with data
    test_file = "/tmp/sentinel_bench_read"
    with open(test_file, "wb") as f:
        f.write(b"A" * 4096)

    fd = os.open(test_file, os.O_RDONLY)

    # Warmup
    for _ in range(100):
        os.lseek(fd, 0, os.SEEK_SET)
        os.read(fd, 4096)

    # Actual benchmark
    for _ in range(ITERATIONS):
        os.lseek(fd, 0, os.SEEK_SET)
        start = time.perf_counter_ns()
        os.read(fd, 4096)
        end = time.perf_counter_ns()
        times.append(end - start)

    os.close(fd)
    os.unlink(test_file)
    return times

def benchmark_write():
    """Benchmark write syscall."""
    times = []
    data = b"B" * 4096

    test_file = "/tmp/sentinel_bench_write"
    fd = os.open(test_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)

    # Warmup
    for _ in range(100):
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, data)

    # Actual benchmark
    for _ in range(ITERATIONS):
        os.lseek(fd, 0, os.SEEK_SET)
        start = time.perf_counter_ns()
        os.write(fd, data)
        end = time.perf_counter_ns()
        times.append(end - start)

    os.close(fd)
    os.unlink(test_file)
    return times

def print_stats(name, times):
    """Print benchmark statistics."""
    mean = statistics.mean(times)
    median = statistics.median(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Iterations:  {len(times):,}")
    print(f"  Mean:        {mean/1000:.2f} µs")
    print(f"  Median:      {median/1000:.2f} µs")
    print(f"  Std Dev:     {stdev/1000:.2f} µs")
    print(f"  P95:         {p95/1000:.2f} µs")
    print(f"  P99:         {p99/1000:.2f} µs")

    return {
        "name": name,
        "iterations": len(times),
        "mean_us": mean / 1000,
        "median_us": median / 1000,
        "stdev_us": stdev / 1000,
        "p95_us": p95 / 1000,
        "p99_us": p99 / 1000
    }

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "native"

    print(f"\n{'#'*60}")
    print(f"  SENTINEL SYSCALL LATENCY BENCHMARK")
    print(f"  Mode: {mode.upper()}")
    print(f"{'#'*60}")

    results = []

    # Run benchmarks
    print("\n[*] Running open/close benchmark...")
    results.append(print_stats("open() + close()", benchmark_open_close()))

    print("\n[*] Running read benchmark...")
    results.append(print_stats("read() 4KB", benchmark_read()))

    print("\n[*] Running write benchmark...")
    results.append(print_stats("write() 4KB", benchmark_write()))

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY ({mode.upper()})")
    print(f"{'='*60}")
    print(f"  {'Syscall':<20} {'Mean (µs)':<15} {'P99 (µs)':<15}")
    print(f"  {'-'*50}")
    for r in results:
        print(f"  {r['name']:<20} {r['mean_us']:<15.2f} {r['p99_us']:<15.2f}")

    # Save results to file
    output_file = f"/tmp/sentinel_bench_{mode}.txt"
    with open(output_file, "w") as f:
        f.write(f"mode={mode}\n")
        for r in results:
            f.write(f"{r['name']}|{r['mean_us']:.2f}|{r['p99_us']:.2f}\n")
    print(f"\n[*] Results saved to {output_file}")

if __name__ == "__main__":
    main()