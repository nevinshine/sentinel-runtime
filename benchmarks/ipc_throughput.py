#!/usr/bin/env python3
"""
Benchmark: IPC Throughput
Measures the latency of Sentinel's named pipe communication.

Usage:
    python3 benchmarks/ipc_throughput.py
"""

import os
import time
import statistics

REQ_PIPE = "/tmp/sentinel_bench_req"
RESP_PIPE = "/tmp/sentinel_bench_resp"
ITERATIONS = 5000

def setup_pipes():
    """Create test pipes."""
    for pipe in [REQ_PIPE, RESP_PIPE]:
        if os.path.exists(pipe):
            os.unlink(pipe)
        os.mkfifo(pipe)

def cleanup_pipes():
    """Remove test pipes."""
    for pipe in [REQ_PIPE, RESP_PIPE]:
        if os.path.exists(pipe):
            os.unlink(pipe)

def run_server():
    """Simple echo server for benchmarking."""
    import threading

    def server_loop():
        with open(REQ_PIPE, "r") as req, open(RESP_PIPE, "w") as resp:
            while True:
                msg = req.readline()
                if not msg or msg.strip() == "QUIT":
                    resp.write("BYE\n")
                    resp.flush()
                    break
                # Simulate brain.py processing
                resp.write("1\n")
                resp.flush()

    t = threading.Thread(target=server_loop, daemon=True)
    t.start()
    return t

def benchmark_ipc():
    """Measure round-trip IPC latency."""
    times = []

    # Start server in background
    server = run_server()
    time.sleep(0.1)  # Let server start

    # Open pipes
    req = open(REQ_PIPE, "w")
    resp = open(RESP_PIPE, "r")

    # Warmup
    for _ in range(100):
        req.write("SYSCALL:test:/tmp/test\n")
        req.flush()
        resp.readline()

    # Benchmark
    for _ in range(ITERATIONS):
        msg = "SYSCALL:openat:/etc/passwd:pid=1234:fd=3:ret=3\n"

        start = time.perf_counter_ns()
        req.write(msg)
        req.flush()
        _ = resp.readline()
        end = time.perf_counter_ns()

        times.append(end - start)

    # Cleanup
    req.write("QUIT\n")
    req.flush()
    resp.readline()
    req.close()
    resp.close()

    return times

def print_stats(name, times):
    """Print benchmark statistics."""
    mean = statistics.mean(times)
    median = statistics.median(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]
    throughput = 1_000_000_000 / mean  # ops per second

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Iterations:   {len(times):,}")
    print(f"  Mean:         {mean/1000:.2f} µs")
    print(f"  Median:       {median/1000:.2f} µs")
    print(f"  Std Dev:      {stdev/1000:.2f} µs")
    print(f"  P95:          {p95/1000:.2f} µs")
    print(f"  P99:          {p99/1000:.2f} µs")
    print(f"  Throughput:   {throughput:,.0f} ops/sec")

def main():
    print(f"\n{'#'*60}")
    print(f"  SENTINEL IPC THROUGHPUT BENCHMARK")
    print(f"{'#'*60}")

    setup_pipes()

    try:
        print("\n[*] Running IPC round-trip benchmark...")
        times = benchmark_ipc()
        print_stats("Named Pipe Round-Trip (req → brain → resp)", times)
    finally:
        cleanup_pipes()

if __name__ == "__main__":
    main()