# Sentinel Runtime Defense System

**Unified Host-Based Intrusion Detection & Network Defense System (HIDS/NIDS)**

**Sentinel Runtime** is a kernel-native security architecture designed to bridge the gap between user-space tracing and kernel-space filtering. Unlike legacy HIDS solutions that rely on high-overhead `ptrace` mechanisms, Sentinel utilizes **Seccomp User Notifications** and **eBPF-LSM** hooks to achieve near-native performance while intercepting critical control plane events.

The system is currently architected to defend against modern Linux threats, specifically targeting "Ghost" I/O (`io_uring`), kernel-resident malware (`bpf` injection), and container escape vectors.

> [!NOTE]
> **Project Status: Active Research (M8.2)**
> * **M4.0 (Stable):** Seccomp-BPF Architecture.
> * **M8.2 (Dev):** eBPF-LSM Migration & "The Bloodline" Inheritance Tracking.
> * **Target:** Research Artifact for CISPA / Saarland University MSc.
> 
> 

## Architectural Pivot: Seccomp vs. Ptrace

In earlier iterations (v3.x), Sentinel employed a `ptrace` loop that paused every system call, resulting in prohibitive performance overhead. In Milestone 4.0, the architecture pivoted to **Seccomp User Notifications** (`SECCOMP_RET_USER_NOTIF`).

| Metric | Legacy M3 (Ptrace) | Modern M4 (Seccomp) | Improvement |
| --- | --- | --- | --- |
| **Interception Model** | Global Pause (All Syscalls) | Filtered (Critical Events Only) | **Selective** |
| **Overhead** | ~54x (Context Switching) | ~1.12x (Near Native) | **98% Reduction** |
| **Throughput** | ~28,000 OPS | ~1,366,558 OPS | **48x Increase** |
| **Race Conditions** | Vulnerable to TOCTOU | Atomic Mitigation (ADDFD) | **Secure** |
| **Blind Spots** | `io_uring`, eBPF loading | Hard Blocked / Trapped | **Covered** |

> [!IMPORTANT]
> **Performance Conclusion**
> For production runtime enforcement, Seccomp provides the necessary performance characteristics while maintaining the ability to inspect critical security boundaries. Sentinel M4 retains **~88% of native throughput** for compute-heavy workloads.

## Core Defense Capabilities

### 1. Anti-Evasion: "Ghost Tunnel" Block

* **Threat Vector:** Malware utilizing `io_uring` to perform asynchronous I/O, bypassing standard syscall auditing tools (e.g., "Curing" Rootkit techniques).
* **Defense Mechanism:** Sentinel enforces a hard block on `io_uring_setup` and `io_uring_enter` at the BPF filter level.
* **Verdict:** `EPERM` is returned instantly, eliminating this evasion path.

### 2. Kernel Integrity: "Invisible Enemy" Trap

* **Threat Vector:** Loading malicious eBPF bytecode to blind security tools or exfiltrate data (e.g., BPFDoor).
* **Defense Mechanism:** Traps the `bpf()` syscall. The Userspace Supervisor analyzes the load attempt and blocks unauthorized programs before they can attach to kernel hooks.

### 3. Anti-TOCTOU: Atomic Injection

* **Threat Vector:** Container escapes (e.g., CVE-2025-31133) utilizing Time-of-Check-Time-of-Use race conditions during file descriptor passing.
* **Defense Mechanism:** Sentinel utilizes `SECCOMP_IOCTL_NOTIF_ADDFD`. The Supervisor opens and verifies the file on behalf of the victim process, then injects the safe File Descriptor directly. The victim never handles the path, rendering path-swapping attacks impossible.

## Performance Benchmarks

Benchmarks were conducted comparing Sentinel M4 against the previous M3 architecture and a Native Linux baseline.

| Metric | Native Linux (Baseline) | Sentinel M4 (Seccomp) | M3 Legacy (Ptrace) |
| --- | --- | --- | --- |
| **Throughput (Fast Path)** | 1,556,510 OPS | 1,366,558 OPS | ~28,000 OPS |
| **Overhead Impact** | 0% | ~12% | ~5400% |
| **Inspection Cost** | 0.130s | 2.313s | >10.0s |

> [!WARNING]
> The increased latency (2.3s) on I/O-heavy tasks reflects the cost of **Deep Semantic Inspection** on every file access. This is a deliberate architectural trade-off prioritizing zero-false-positive security over raw I/O speed.

## Roadmap: Evolution to eBPF (M8)

Sentinel is currently transitioning from Phase 2 (Seccomp/M4) to Phase 3 (eBPF-LSM/M8) to address advanced evasion techniques used by targeted threat actors.

* **M5: "Project Ocular" (Observability Gap) [COMPLETED]**
* *Problem:* Seccomp lacks deep argument inspection (pointer dereferencing).
* *Solution:* Introduced eBPF `fentry` hooks for deep argument inspection, replacing Python loggers with C-based BPF ring buffers.


* **M6: "The Iron Gate" (LSM Migration) [COMPLETED]**
* *Problem:* Seccomp is strictly syscall-entry based.
* *Solution:* Migrated enforcement to LSM Hooks (`security_bprm_check`, `security_file_open`). Enforcement now occurs after kernel path resolution.


* **M7: "The Bloodline" (Inheritance Tracking) [COMPLETED]**
* *Problem:* Malicious processes rapidly forking to evade supervisor attachment.
* *Solution:* Implemented Kernel-Space Lineage Tracking using `BPF_MAP_TYPE_HASH` to atomically enforce policy inheritance at `task_alloc`.


* **M8: "Citadel" (Current Release Candidate) [ACTIVE]**
* *Focus:* Fileless Malware & Memory Defense.
* *Features:* Anti-Memfd (hooks `memfd_create`), Anti-LD_PRELOAD injection.



## Usage (M4.0)

### 1. Build The Engine

Requires `libseccomp-dev`.

```bash
make clean && make

```

### 2. Start The Defense Grid

The architecture requires running the Logic Core (Brain) and the Interceptor (Body) simultaneously.

**Terminal 1: The Brain (Logic)**

```bash
python3 src/analysis/brain.py

```

**Terminal 2: The Body (Interceptor)**

```bash
# Protect a shell (and all its children)
sudo ./bin/sentinel /bin/bash

```

## Repository Structure

```text
sentinel-runtime/
├── bin/                    # Compiled Binaries (M4)
├── src/
│   ├── engine/             # [C] Seccomp Interceptor (M4)
│   │   ├── main.c          # Seccomp-BPF & ADDFD Logic
│   │   └── fdmap.c         # File Descriptor Tracking
│   ├── analysis/           # [Python] Semantic Supervisor
│   │   ├── brain.py        # Decision Core
│   │   └── semantic.py     # Path Classification
│   └── lsm/                # [C/BPF] eBPF-LSM Engine (M8)
│       ├── sentinel_lsm.c  # BPF Program (Exec/Fork/GC)
│       └── tests/          # Red Team Tools (Torture/Jailbreak)
├── docs/
│   └── MITRE_MAPPING.md    # ATT&CK Framework Alignment
└── benchmarks/             # Performance Data

```

## Citation

```bibtex
@software{sentinel2026,
  author      = {Nevin Shine},
  title       = {Sentinel M4: Kernel Supervision via Seccomp User Notification},
  year        = {2026},
  version     = {V4.0.0},
  institution = {Research Artifact},
  url         = {https://github.com/nevinshine/sentinel-runtime}
}

```
---

Nevin Shine (System Security Student) @ 2026
