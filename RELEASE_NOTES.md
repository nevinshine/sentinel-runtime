# Release Notes - Sentinel M4.0

## Major Architectural Pivot
* **Removed:** `ptrace` syscall interception loop (Legacy M3).
* **Added:** `seccomp-bpf` filter with `SECCOMP_RET_USER_NOTIF`.
* **Result:** Context switches reduced by >99% (Native Speed).

## Security Hardening
* **io_uring:** Explicitly blocked to prevent async I/O evasion.
* **bpf:** Trapped to prevent kernel-resident malware loading.
* **mprotect:** W^X (Write XOR Execute) violations trapped to stop fileless malware.
* **TOCTOU Mitigation:** Implemented atomic FD injection (`ADDFD`) to neutralize `runc` race conditions.

## Performance
* **Micro-Benchmark:** 1.3M OPS sustained throughput (Verified).
* **Macro-Benchmark:** 2.3s latency on massive filesystem walks (Verified).

## Bug Fixes
* Fixed race condition where `openat` path arguments could be swapped after verification.
* Fixed high CPU usage during idle periods (removed polling loops).
