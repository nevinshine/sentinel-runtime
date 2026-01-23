# Sentinel Runtime Benchmarks

## Overview

Performance benchmarks for Sentinel Runtime measuring syscall interception overhead, IPC latency, and memory usage.

## Test Environment

| Component | Specification |
|-----------|---------------|
| OS | Ubuntu 22.04 LTS |
| Kernel | 6.x (update with `uname -r`) |
| CPU | (update with `lscpu \| grep "Model name"`) |
| RAM | (update with `free -h`) |
| Python | 3.10+ |

## Benchmarks

### 1. Syscall Latency

Measures per-syscall overhead comparing native execution vs Sentinel-traced execution.

**Methodology:**
- 10,000 iterations per syscall
- Nanosecond precision timing (`time.perf_counter_ns()`)
- Warmup phase to eliminate cold-start effects

**Results:**

| Syscall | Native (µs) | Traced (µs) | Overhead |
|---------|-------------|-------------|----------|
| open() + close() | 15.01 | 341.79 | 22.8x |
| read() 4KB | 3.09 | 114.81 | 37.2x |
| write() 4KB | 5.84 | 120.45 | 20.6x |

**Analysis:**
- Overhead is consistent with ptrace-based interception (context switches)
- Each traced syscall requires: stop → inspect → IPC → verdict → resume
- The ~100-350µs overhead is acceptable for security monitoring use cases

---

### 2. IPC Throughput

Measures named pipe communication latency between C engine and Python brain.

**Methodology:**
- 5,000 round-trip message exchanges
- Simulates real syscall event → verdict flow

**Results:**

| Metric | Value |
|--------|-------|
| Mean Latency | 34.93 µs |
| Median Latency | 31.54 µs |
| P95 Latency | 48.22 µs |
| P99 Latency | 70.20 µs |
| Throughput | 28,628 ops/sec |

**Analysis:**
- IPC adds ~35µs per syscall decision
- Throughput of ~28K ops/sec is sufficient for most workloads
- Named pipes provide reliable, ordered communication

---

### 3. Memory Profile

Tracks RAM usage of Sentinel components during operation.

**Results:**

| Component | RAM Usage |
|-----------|-----------|
| Sentinel (C engine) | ~88 MB |
| Brain (Python) | ~12 MB |
| **Total** | **~100 MB** |

**Analysis:**
- Memory footprint is reasonable for a security monitor
- C engine holds process tracking arrays (MAX_PIDS)
- Python brain includes semantic knowledge base

---

## Overhead Context

| System | Typical Overhead | Notes |
|--------|------------------|-------|
| **Sentinel** | 20-40x | ptrace + IPC + Python analysis |
| strace | 10-30x | ptrace only, no analysis |
| eBPF-based | 1.5-3x | Kernel-native, no context switch |
| seccomp | 1.1-1.5x | Kernel filtering only |

Sentinel's overhead is higher due to:
1. **ptrace context switches** (kernel ↔ userspace)
2. **IPC round-trip** (C → Python → C)
3. **Semantic analysis** (pattern matching, state machine)

This is acceptable for:
- Security research and testing
- Malware analysis sandboxes
- Development/debugging environments

For production workloads, consider eBPF-based approaches.

---

## Running Benchmarks

```bash
# Syscall latency (native baseline)
python3 benchmarks/syscall_latency.py native

# Syscall latency (traced)
# Terminal 1: cd src/analysis && python3 brain.py
# Terminal 2: sudo ./bin/sentinel test python3 benchmarks/syscall_latency.py traced

# IPC throughput
python3 benchmarks/ipc_throughput.py

# Memory profile (while Sentinel is running)
python3 benchmarks/memory_profile.py 60

# Workload stress tests
./benchmarks/workloads/file_stress.sh 1000
./benchmarks/workloads/process_stress.sh 500
```

---

## Conclusion

Sentinel introduces measurable overhead (~20-40x per syscall) due to its ptrace-based architecture. This trade-off enables:

- ✅ Deep syscall inspection
- ✅ Cross-process taint tracking
- ✅ Real-time blocking capability
- ✅ No kernel module required

The overhead is acceptable for security research, malware analysis, and development environments.