# 🚧 Status: M8.0 Architecture Migration (Active Research)

> **Current Focus:** Migrating core logic from Phase 2 (Seccomp) to **Phase 3 (eBPF-LSM)**.  
> - **Active Development:** Implementing **"The Bloodline"** (Process Inheritance Tracking) and `memfd_create` blocking in Ring 0.  
> - **Performance Goal:** Reducing overhead from ~12% (M4) to **<5µs** (M8) using kernel-native hooks.  
> - **Latest Branch:** See `dev-ebpf` for active C/Kernel code.

---

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

  [RUNTIME STATUS]
  > VERSION:       M4.0 (Seccomp Architecture) -> Migrating to M8 (eBPF)
  > ENGINE:        C (Seccomp-BPF + User Notification)
  > BRAIN:         Python (Deterministic State Machine)
  > FIREWALL:      Hyperion XDP (Bridge Active)
  > TARGET:        Research Artifact (CISPA / Saarland MSc)
```

⸻

[ 0x01 ] ABSTRACT

Sentinel represents a paradigm shift from user-space tracing (ptrace) to kernel-space filtering.

Unlike legacy HIDS that suffer from significant overhead, Sentinel achieves native speed for 99% of operations by intercepting only critical control-plane events (execve, openat, connect) while offloading deep analysis to a userspace supervisor.

The architecture introduces Architectural Hardening against modern Linux threats, specifically targeting Ghost I/O and kernel-resident malware.

Read the MITRE Mapping for a technical deep dive into Sentinel’s ATT&CK alignment.

⸻

[ 0x02 ] ARCHITECTURAL PIVOT: SECCOMP vs PTRACE

Earlier iterations (v3.x) paused every syscall using ptrace.

Milestone 4 pivoted to Seccomp User Notifications (SECCOMP_RET_USER_NOTIF).

Feature	Legacy M3 (Ptrace)	Modern M4 (Seccomp)
Interception	All syscalls	Filtered
Overhead	~54x	~1.12x
Throughput	~28k OPS	~1.36M OPS
Race Conditions	TOCTOU vulnerable	Atomic mitigation
Blind Spots	io_uring, eBPF	Trapped

Conclusion: Seccomp offers production-grade performance while preserving inspection.

⸻

[ 0x03 ] CRITICAL DEFENSE CAPABILITIES (M4)

1. Ghost Tunnel Block
	•	Threat: io_uring evasion (e.g., Curing rootkit)
	•	Defense: Hard-blocks io_uring_setup and io_uring_enter
	•	Verdict: EPERM returned instantly

2. Invisible Enemy Trap
	•	Threat: Malicious eBPF loaders (e.g., BPFDoor)
	•	Defense: Traps bpf() syscall and analyzes before load

3. Atomic Injection
	•	Threat: runc TOCTOU escapes (CVE-2025-31133)
	•	Defense: Uses SECCOMP_IOCTL_NOTIF_ADDFD
	•	Result: Victim never touches the path

⸻

[ 0x04 ] PERFORMANCE BENCHMARKS

Metric	Native	Sentinel M4	M3
Throughput	1.56M OPS	1.36M OPS	28k
Overhead	0%	~12%	5400%
Inspection Cost	0.13s	2.3s	>10s

Sentinel M4 preserves ~88% of native speed while enforcing zero-false-positive inspection.

⸻

[ 0x05 ] USAGE (M4)

Build

```
sudo apt install libseccomp-dev
make clean && make
```

Run

Terminal 1 — Brain:

```
python3 src/analysis/brain.py
```

Terminal 2 — Interceptor:

```
sudo ./bin/sentinel /bin/bash
```

⸻

[ 0x06 ] TECHNICAL SPECIFICATIONS

Auto-DLP Bridge
	1.	User opens top_secret.pdf
	2.	Brain tags as sensitive
	3.	Filename written to signatures.txt
	4.	Hyperion XDP drops matching packets

⸻

[ 0x07 ] ROADMAP TO M8

M5 — Project Ocular
	•	Added eBPF argument inspection
	•	Replaced Python ptrace logger
	•	Status: Completed

M6 — Iron Gate
	•	Migrated to LSM hooks
	•	Eliminated TOCTOU
	•	Status: Completed

M7 — Bloodline
	•	Kernel lineage tracking
	•	BPF_MAP_TYPE_HASH
	•	Status: Completed

M8 — Citadel
	•	memfd_create detection
	•	LD_PRELOAD defense
	•	<5µs latency target
	•	Status: Active Research

⸻

[ 0x08 ] PROJECT STRUCTURE

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

⸻

[ 0x09 ] CITATION

```
@software{sentinel2026,
  author = {Nevin Shine},
  title = {Sentinel M4: Kernel Supervision via Seccomp User Notification},
  year = {2026},
  version = {V4.0.0},
  institution = {Research Artifact},
  url = {https://github.com/nevinshine/sentinel-runtime}
}
```
