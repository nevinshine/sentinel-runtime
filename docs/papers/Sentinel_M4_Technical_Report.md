# Sentinel M4: High-Performance Kernel Supervision via Seccomp User Notification

**Author:** Nevin  
**Date:** February 2026  
**Artifact:** Sentinel Runtime M4.0  
**Repository:** [github.com/nevinshine/sentinel-runtime](https://github.com/nevinshine/sentinel-runtime)

---

## Abstract

Runtime security in Linux has traditionally relied on `ptrace`-based system call interposition, a mechanism that introduces prohibitive performance overhead (often exceeding 50x) due to excessive context switching. This paper presents **Sentinel M4**, a novel host-based intrusion detection system (HIDS) that leverages **Seccomp-BPF** with **User Notification** (`SECCOMP_RET_USER_NOTIF`) to achieve near-native performance. Sentinel M4 introduces a hybrid "Block-Trap-Inject" architecture that neutralizes modern kernel threats—including asynchronous I/O evasion (`io_uring`), kernel-resident malware (eBPF roots), and container escape race conditions (TOCTOU)—while retaining 88% of native system throughput.

---

## 1. Introduction

As adversaries move down the stack from application exploits to kernel-native evasion techniques, traditional security agents are struggling to maintain visibility without degrading performance. Legacy architectures typically rely on:
1.  **Ptrace:** Universal interception but high latency (stop-the-world).
2.  **LD_PRELOAD:** Fast but easily bypassed by static binaries or direct syscalls.
3.  **Kernel Modules (LKM):** High risk of kernel panic and maintenance debt.

Sentinel M4 proposes a fourth approach: **Cooperative Kernel Supervision**. By using the Linux Kernel's native Seccomp filter to "whitelist" safe operations in-kernel, Sentinel eliminates the context-switch tax for 99% of system calls, waking the userspace supervisor only for critical control-plane events.

---

## 2. Threat Model

Sentinel M4 is architected to defend against three specific classes of advanced persistent threats (APTs) identified in the 2025-2026 Linux Threat Landscape:

### 2.1. The "Ghost Tunnel" (Async I/O Evasion)
Adversaries utilize `io_uring` to perform filesystem and network operations asynchronously. Since standard auditing tools hook synchronous syscalls (e.g., `read`, `write`), `io_uring` operations bypass detection entirely.
* **Attack Vector:** "Curing" Rootkit.
* **Sentinel Defense:** Pre-emptive blocking of `io_uring_setup` syscalls for untrusted processes.

### 2.2. The "Invisible Enemy" (Kernel-Resident Malware)
Sophisticated malware loads malicious eBPF programs to manipulate kernel return values (`bpf_override_return`) or hide process artifacts from userspace tools.
* **Attack Vector:** BPFDoor / Symbiote.
* **Sentinel Defense:** Trapping the `bpf()` syscall to inspect and authorize bytecode loading.

### 2.3. Container Escapes (TOCTOU Races)
Vulnerabilities in container runtimes (e.g., CVE-2025-31133 in `runc`) exploit the time gap between file path verification and file opening (Time-of-Check-Time-of-Use).
* **Attack Vector:** Symlink swapping during container initialization.
* **Sentinel Defense:** Atomic File Descriptor Injection (`SECCOMP_IOCTL_NOTIF_ADDFD`).

---

## 3. System Architecture

Sentinel M4 implements a split-brain architecture:

### 3.1. The Kernel Filter (BPF)
A classic Berkeley Packet Filter loaded via `prctl`. It acts as the first line of defense:
* **ALLOW:** High-frequency, low-risk calls (`read`, `write`, `clock_gettime`, `getpid`).
* **ERRNO:** Explicitly dangerous calls (`io_uring_setup`, `init_module`).
* **NOTIFY:** Control-plane calls requiring inspection (`execve`, `openat`, `connect`, `bpf`).

### 3.2. The Userspace Supervisor (C Engine)
A lightweight C daemon that listens on the Seccomp Notification File Descriptor. It handles:
* **Context Retrieval:** Reading target memory via `process_vm_readv`.
* **Atomic Injection:** Using `ADDFD` to open files on the host and inject the verified file descriptor into the target, eliminating race conditions.

### 3.3. The Neural Brain (Python)
A high-level decision engine running a deterministic State Machine. It maintains the "Kill Chain" context for every process tree.
* **Input:** JSON-serialized events from the C Engine.
* **Logic:** Semantic path analysis and behavioral heuristics.
* **Output:** ALLOW/BLOCK verdicts.

---

## 4. Implementation Details

### 4.1. Atomic Injection Logic
To mitigate TOCTOU attacks, Sentinel never allows the target to open a file directly.
1.  **Trap:** Target calls `openat("/etc/passwd")`. Kernel pauses Target.
2.  **Verify:** Sentinel inspects the path.
3.  **Open:** Sentinel opens `/etc/passwd` in its own memory space.
4.  **Inject:** Sentinel calls `ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_ADDFD, ...)` to insert the FD into the Target.
5.  **Emulate:** Sentinel tells the kernel to cancel the original syscall and return the injected FD number.

### 4.2. Performance Optimization
The transition from M3 (Ptrace) to M4 (Seccomp) removed the "Ptrace Loop."
* **M3:** Syscall -> Trap -> Wake Sentinel -> Inspect -> Resume -> Execute. (2 Context Switches per Syscall).
* **M4:** Syscall -> BPF Check (In-Kernel) -> Execute. (0 Context Switches for safe calls).

---

## 5. Evaluation

We evaluated Sentinel M4 on a standard Linux workstation (Fedora 41, Kernel 6.12) against the legacy M3 architecture.

### 5.1. Micro-Benchmark: System Call Throughput
Measured using a tight loop of 10 million `getpid` calls.

| Architecture | Throughput (OPS) | Overhead |
| :--- | :--- | :--- |
| Native Linux | 1,556,510 | 0% |
| **Sentinel M4** | **1,366,558** | **~12%** |
| Sentinel M3 | ~28,000 | ~5400% |

**Result:** Sentinel M4 retains 88% of native throughput, making it suitable for high-performance production workloads.

### 5.2. Macro-Benchmark: I/O Latency
Measured using a recursive `find` and `grep` operation across 10,000 files.

| Architecture | Wall Clock Time | Analysis |
| :--- | :--- | :--- |
| Native Linux | 0.130s | Baseline disk I/O. |
| **Sentinel M4** | **2.313s** | Cost of deep inspection per file open. |

**Result:** While throughput remains high, latency increases for I/O-heavy operations due to the round-trip cost of the Python decision engine. This is an acceptable trade-off for the security guarantees provided.

### 5.3. Security Verification
| Attack Vector | Test Tool | Sentinel M4 Verdict |
| :--- | :--- | :--- |
| **Ghost Tunnel** | `io_uring_setup` PoC | **BLOCKED (EPERM)** |
| **Invisible Enemy** | `bpf()` loader | **TRAPPED & LOGGED** |
| **Fileless Malware** | `mprotect(PROT_EXEC)` | **BLOCKED** |
| **Process Storm** | `recursive_fork` | **STABLE (No Crash)** |

---

## 6. Conclusion

Sentinel M4 demonstrates that high-security kernel supervision does not require a compromise on system stability or performance. By leveraging modern Linux kernel features (Seccomp User Notifications), we achieved a 50x performance improvement over legacy Ptrace architectures while simultaneously closing critical evasion gaps like `io_uring` and race conditions. Future work will focus on porting the "Neural Brain" logic to eBPF maps to further reduce the I/O latency observed in macro-benchmarks.

---
**Citation:**
Nevin. (2026). *Sentinel M4: Kernel Supervision via Seccomp User Notification*. Research Artifact.
