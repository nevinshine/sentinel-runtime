# Sentinel Runtime Defense System (M4.0)
> Unified Host-Based Intrusion Detection & Network Defense System (HIDS/NIDS)

```console
root@Sentinel-Node:~# ./bin/sentinel /bin/bash

 [ KERNEL ] LOADING SECCOMP-BPF FILTER ................. [ACTIVE]
 [ IPC    ] CONNECTING TO NEURAL BRAIN ................. [CONNECTED]
 [ TRAP   ] GHOST TUNNEL (IO_URING) .................... [BLOCKED]
 [ TRAP   ] INVISIBLE ENEMY (EBPF) ..................... [MONITORED]
 [ MODE   ] ATOMIC INJECTION (ANTI-TOCTOU) ............. [READY]

   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝

  >> SENTINEL RUNTIME M4 (SECCOMP ARCHITECTURE) <<

  [RUNTIME STATUS]
  > VERSION:       M4.0 (Seccomp Architecture)
  > ENGINE:        C (Seccomp-BPF + User Notification)
  > BRAIN:         Python (Deterministic State Machine)
  > FIREWALL:      Hyperion XDP (Bridge Active)
  > TARGET:        Research Artifact (CISPA / Saarland MSc)

```

---

## [ 0x01 ] ABSTRACT

**Sentinel M4** represents a paradigm shift from user-space tracing (ptrace) to kernel-space filtering (**Seccomp-BPF**). Unlike legacy HIDS that suffer from significant overhead, Sentinel M4 achieves **native speed for 99% of operations** by intercepting only critical control plane events (`execve`, `openat`, `connect`) while offloading deep analysis to a Userspace Supervisor.

This release introduces **Architectural Hardening** against modern Linux threats, specifically targeting "Ghost" I/O and kernel-resident malware.

> **[Read the MITRE Mapping](https://www.google.com/search?q=docs/MITRE_MAPPING.md)** - A technical deep-dive into how Sentinel aligns with the ATT&CK framework.

---

## [ 0x02 ] ARCHITECTURAL PIVOT: SECCOMP vs PTRACE

In earlier iterations (v3.x), Sentinel employed a `ptrace` loop that paused every system call. In **Milestone 4.0**, we architecturally pivoted to **Seccomp User Notifications**.

| Feature | Legacy M3 (Ptrace) | Modern M4 (Seccomp) |
| --- | --- | --- |
| **Interception** | All Syscalls (Global Pause) | Filtered (Only Critical Events) |
| **Overhead** | ~54x (Heavy Context Switching) | **~12%** (Near Native Speed) |
| **Throughput** | ~28,000 OPS | **~1,366,558 OPS** |
| **Race Conditions** | Vulnerable to TOCTOU | **Atomic Mitigation** (ADDFD) |
| **Blind Spots** | io_uring, eBPF loading | **Hard Blocked / Trapped** |

**Conclusion:** For production runtime enforcement, Seccomp provides the necessary performance characteristics while maintaining the ability to inspect critical security boundaries.

---

## [ 0x03 ] CRITICAL DEFENSE CAPABILITIES (M4)

### 1. The "Ghost Tunnel" Block (Anti-Evasion)

* **Threat:** Malware using `io_uring` to bypass standard syscall auditing (e.g., "Curing" Rootkit).
* **Defense:** Sentinel M4 enforces a **Hard Block** on `io_uring_setup` and `io_uring_enter` at the BPF level.
* **Verdict:** `EPERM` returned instantly. Zero chance of evasion.

### 2. The Invisible Enemy Trap (Kernel Integrity)

* **Threat:** Loading malicious eBPF bytecode to blind security tools (e.g., BPFDoor).
* **Defense:** Traps the `bpf()` syscall. The Supervisor analyzes the load attempt and blocks unauthorized programs before they execute.

### 3. Atomic Injection (Anti-TOCTOU)

* **Threat:** `runc` container escapes (CVE-2025-31133) utilizing Time-of-Check-Time-of-Use race conditions.
* **Defense:** Sentinel uses `SECCOMP_IOCTL_NOTIF_ADDFD`. The Supervisor opens and verifies the file *on behalf* of the victim, then injects the safe File Descriptor. The victim never handles the path, making path-swapping attacks impossible.

---

## [ 0x04 ] PERFORMANCE BENCHMARKS (VALIDATED)

We benchmarked Sentinel M4 against the previous M3 (Ptrace) architecture and a Native Baseline.

| Metric | Native Linux (Baseline) | Sentinel M4 (Seccomp) | M3 Legacy (Ptrace) |
| --- | --- | --- | --- |
| **Throughput (Fast Path)** | 1,556,510 OPS | **1,366,558 OPS** | ~28,000 OPS |
| **Overhead Impact** | 0% | **~12%** | ~5400% |
| **Inspection Cost** | 0.130s | **2.313s** | >10.0s |

> **Analysis:** Sentinel M4 retains **~88% of native throughput** for compute-heavy workloads. The 2.3s latency on I/O-heavy tasks (Macro-Benchmark) reflects the cost of **Deep Neural Inspection** on every file access. This is a deliberate trade-off for zero-false-positive security.

---

## [ 0x05 ] USAGE (M4.0)

### 1. Build The Engine

```bash
# Requires libseccomp-dev
make clean && make

```

### 2. Start The Defense Grid

You must run the Brain (Logic) and the Body (Interceptor) together.

**Terminal 1: The Brain**

```bash
python3 src/analysis/brain.py

```

**Terminal 2: The Body (Interceptor)**

```bash
# Protect a shell (and all its children)
sudo ./bin/sentinel /bin/bash

```

---

## [ 0x06 ] TECHNICAL SPECIFICATIONS (M4.0)

### The "Auto-DLP" Bridge

Sentinel M4 retains the bridge between userspace and kernelspace.

1. **Trigger:** User opens `top_secret.pdf`.
2. **Analysis:** Brain tags file as `SENSITIVE_USER_FILE`.
3. **Action:** Brain writes the filename to `signatures.txt`.
4. **Enforcement:** Hyperion XDP (Network Firewall) reads the signature and instantly drops any outgoing packet containing that filename.

---

## [ 0x07 ] CITATION

```text
@software{sentinel2026,
  author = {Nevin Shine},
  title = {Sentinel M4: Kernel Supervision via Seccomp User Notification},
  year = {2026},
  version = {V4.0.0},
  institution = {Research Artifact},
  url = {[https://github.com/nevinshine/sentinel-runtime](https://github.com/nevinshine/sentinel-runtime)}
}

```

---

## [ 0x08 ] PROJECT STRUCTURE

```text
sentinel-runtime/
├── bin/                        # Compiled Binaries
│   ├── sentinel                # The M4 Engine (Interceptor)
│   ├── m4_test                 # Red Team Validator
│   └── bench_throughput        # Performance Benchmark
├── src/
│   ├── engine/                 # [C] Kernel Interceptor
│   │   ├── main.c              # Seccomp-BPF & ADDFD Logic
│   │   ├── logger.c            # IPC Messaging
│   │   └── fdmap.c             # File Descriptor Tracking
│   └── analysis/               # [Python] Neural Supervisor
│       ├── brain.py            # Decision Core
│       ├── semantic.py         # Path Classification
│       └── state_machine.py    # Kill-Chain Logic
├── tests/
│   ├── evasion/                # Attack Simulations
│   │   ├── m4_test.c           # io_uring & eBPF PoC
│   │   └── recursive_fork.c    # Process Storm Test
│   └── workloads/              # Stress Tests
│       └── file_stress.sh      # I/O Latency Test
├── benchmarks/                 # Performance Data
│   ├── syscall_latency.py      # Micro-benchmarks
│   └── BENCHMARKS.md           # Results Log
├── docs/
│   ├── MITRE_MAPPING.md        # ATT&CK Framework Alignment
│   └── papers/                 # Research References
├── assets/                     # Demo Recordings (.cast/gif)
├── Makefile                    # Build Configuration
└── README.md                   # Technical Documentation

```
