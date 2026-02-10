# Sentinel Runtime Defense System

> Unified Host-Based Intrusion Detection & Network Defense System (HIDS/NIDS)

```console
root@Sentinel-Node:~# ./bin/sentinel /bin/bash

 [ KERNEL ] LOADING SECCOMP-BPF FILTER ................. [ACTIVE]
 [ IPC    ] CONNECTING TO SEMANTIC BRAIN ............... [CONNECTED]
 [ TRAP   ] GHOST TUNNEL (IO_URING) .................... [BLOCKED]
 [ TRAP   ] INVISIBLE ENEMY (EBPF) ..................... [MONITORED]
 [ MODE   ] ATOMIC INJECTION (ANTI-TOCTOU) ............. [READY]

   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝

  >> SENTINEL RUNTIME (SECCOMP ARCHITECTURE) <<

  [ 🚧 CURRENT STATUS: M8.0 ACTIVE RESEARCH ]
  > FOCUS:         Migrating Core Logic (Seccomp -> eBPF-LSM)
  > FEATURE:       "The Bloodline" (Inheritance Tracking) & Anti-Memfd
  > GOAL:          <5µs Latency (Kernel-Native Enforcement)
  > BRANCH:        See 'dev-ebpf' for active C code

  [RUNTIME METADATA]
  > VERSION:       M4.0 (Stable) -> M8.0 (In Development)
  > ENGINE:        C (Seccomp-BPF + User Notification)
  > FIREWALL:      Hyperion XDP (Bridge Active)
  > TARGET:        Research Artifact (CISPA / Saarland MSc)
```

-----

## [0x01] Abstract

Sentinel represents a paradigm shift from user-space tracing (`ptrace`) to kernel-space filtering. Unlike legacy HIDS that suffer from significant overhead, Sentinel achieves native speed for 99% of operations by intercepting only critical control plane events (`execve`, `openat`, `connect`) while offloading deep analysis to a Userspace Supervisor.

The current architecture introduces Architectural Hardening against modern Linux threats, specifically targeting “Ghost” I/O and kernel-resident malware.

> 📄 Read the [MITRE Mapping](docs/MITRE_MAPPING.md) — A technical deep-dive into how Sentinel aligns with the ATT&CK framework.

-----

## [0x02] Architectural Pivot: Seccomp vs Ptrace

In earlier iterations (v3.x), Sentinel employed a `ptrace` loop that paused every system call. In Milestone 4.0, we architecturally pivoted to Seccomp User Notifications (`SECCOMP_RET_USER_NOTIF`).

|Feature        |Legacy M3 (Ptrace)            |Modern M4 (Seccomp)            |
|---------------|------------------------------|-------------------------------|
|Interception   |All Syscalls (Global Pause)   |Filtered (Only Critical Events)|
|Overhead       |~54x (Heavy Context Switching)|~1.12x (Near Native Speed)     |
|Throughput     |~28,000 OPS                   |~1,366,558 OPS                 |
|Race Conditions|Vulnerable to TOCTOU          |Atomic Mitigation (ADDFD)      |
|Blind Spots    |`io_uring`, eBPF loading      |Hard Blocked / Trapped         |

**Conclusion:** For production runtime enforcement, Seccomp provides the necessary performance characteristics while maintaining the ability to inspect critical security boundaries.

-----

## [0x03] Critical Defense Capabilities (M4)

### 1. The “Ghost Tunnel” Block (Anti-Evasion)

- **Threat:** Malware using `io_uring` to bypass standard syscall auditing (e.g., “Curing” Rootkit).
- **Defense:** Sentinel M4 enforces a Hard Block on `io_uring_setup` and `io_uring_enter` at the BPF level.
- **Verdict:** `EPERM` returned instantly. Zero chance of evasion.

### 2. The Invisible Enemy Trap (Kernel Integrity)

- **Threat:** Loading malicious eBPF bytecode to blind security tools (e.g., BPFDoor).
- **Defense:** Traps the `bpf()` syscall. The Supervisor analyzes the load attempt and blocks unauthorized programs before they execute.

### 3. Atomic Injection (Anti-TOCTOU)

- **Threat:** `runc` container escapes (CVE-2025-31133) utilizing Time-of-Check-Time-of-Use race conditions.
- **Defense:** Sentinel uses `SECCOMP_IOCTL_NOTIF_ADDFD`. The Supervisor opens and verifies the file on behalf of the victim, then injects the safe File Descriptor. The victim never handles the path, making path-swapping attacks impossible.

-----

## [0x04] Performance Benchmarks (Validated)

We benchmarked Sentinel M4 against the previous M3 (Ptrace) architecture and a Native Baseline.

|Metric                |Native Linux (Baseline)|Sentinel M4 (Seccomp)|M3 Legacy (Ptrace)|
|----------------------|-----------------------|---------------------|------------------|
|Throughput (Fast Path)|1,556,510 OPS          |1,366,558 OPS        |~28,000 OPS       |
|Overhead Impact       |0%                     |~12%                 |~5400%            |
|Inspection Cost       |0.130s                 |2.313s               |>10.0s            |


> **Analysis:** Sentinel M4 retains ~88% of native throughput for compute-heavy workloads. The 2.3s latency on I/O-heavy tasks (Macro-Benchmark) reflects the cost of Deep Semantic Inspection on every file access. This is a deliberate trade-off for zero-false-positive security.

-----

## [0x05] Usage (M4.0)

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

-----

## [0x06] Technical Specifications (M4.0)

### The “Auto-DLP” Bridge

Sentinel M4 retains the bridge between userspace and kernelspace.

1. **Trigger:** User opens `top_secret.pdf`.
1. **Analysis:** Brain tags file as `SENSITIVE_USER_FILE`.
1. **Action:** Brain writes the filename to `signatures.txt`.
1. **Enforcement:** Hyperion XDP (Network Firewall) reads the signature and instantly drops any outgoing packet containing that filename.

-----

## [0x07] Roadmap: The Evolution to M8 (eBPF)

Sentinel is currently transitioning from Phase 2 (Seccomp/M4) to Phase 3 (eBPF-LSM/M8) to address advanced evasion techniques used by targeted threat actors.

### M5: “Project Ocular” (Observability Gap)

- **Problem:** Seccomp could block calls, but couldn’t see data (e.g., it sees `openat` but not the filename if the pointer is complex).
- **Solution:** Introduced eBPF `fentry` hooks for deep argument inspection.
- **Status:** ✅ Completed. Replaced Python ptrace logger with C-based BPF ring buffers.

### M6: “The Iron Gate” (LSM Migration)

- **Problem:** Seccomp is vulnerable to Time-of-Check-Time-of-Use (TOCTOU) races in complex container environments.
- **Solution:** Migrated enforcement from syscall-entry (Seccomp) to LSM Hooks (`security_bprm_check`, `security_file_open`).
- **Impact:** Enforcement now happens after the kernel resolves paths, eliminating race conditions.
- **Status:** ✅ Completed (Core Engine Ported).

### M7: “The Bloodline” (Inheritance Tracking)

- **Problem:** The “Fork Loophole.” A malicious process could `fork()` rapidly, and the child would execute before the userspace supervisor could attach.
- **Solution:** Implemented Kernel-Space Lineage Tracking.
  - Used `BPF_MAP_TYPE_HASH` to store parent-child relationships.
  - Enforced policy inheritance atomically at `task_alloc`.
- **Status:** ✅ Completed. (This is the “Fork-Evasion” fix).

### M8: “Citadel” (Current Release Candidate)

- **Focus:** Fileless Malware & Memory Defense.
- **Features:**
  - **Anti-Memfd:** Hooks `memfd_create` to detect fileless ELF loading (TeamTNT tactic).
  - **Ghost-Buster:** Detects `LD_PRELOAD` injection attempts.
  - **Optimization:** Code path optimized to `<5µs` latency.
- **Status:** 🚧 Active Research.

-----

## [0x08] Project Structure

```
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
│   └── analysis/               # [Python] Semantic Supervisor
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

-----

## [0x09] Citation

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
