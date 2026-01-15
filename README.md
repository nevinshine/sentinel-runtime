# Sentinel Runtime

![Milestone](https://img.shields.io/badge/milestone-M1.2_semantic-blue?style=flat-square)
![Experimental](https://img.shields.io/badge/experimental-M2.0_process_tree-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-systems_security_research-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Research Artifact
> **Stable Milestone:** M1.2 (Semantic Enforcement)
> **Current Experimental Milestone:** M2.0 (Process Tree Tracking)

## Abstract

**Sentinel Runtime** is a Linux runtime defense system designed to investigate syscall-level observability and semantic enforcement.

Unlike traditional signature-based AVs, Sentinel leverages `ptrace` to establish a closed-loop runtime control system. It connects a high-speed C interception kernel to a Python-based Weightless Neural Network (WiSARD) to evaluate process intent against security policies in real-time.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## Capability Milestone Status

| Feature | Milestone | Status | Description |
| :--- | :--- | :--- | :--- |
| **Deep Introspection** | M0.8 | ✅ **Validated** | Argument extraction via `PTRACE_PEEKDATA`. |
| **Online Inference Loop** | M1.0 | ✅ **Validated** | Prototype real-time decision pipeline (latency under evaluation). |
| **Active Blocking** | M1.1 | ✅ **Validated** | **Enforcement Semantics.** Injecting `ENOSYS` to neutralize malicious syscalls. |
| **Semantic Enforcement**| M1.2 | ✅ **Validated** | Context-aware policy evaluation (e.g., allow `mkdir`, block `mkdir malware`). |
| **Process Tree Tracking** | M2.0 | 🧪 **Experimental** | **Recursive Fork Monitoring.** Tracing dynamic process trees via `PTRACE_O_TRACEFORK`. |

---

## Architecture

Sentinel operates as a closed-loop runtime control system:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/`*
- **Interception Engine:** A recursive `ptrace` monitor that handles `PTRACE_EVENT_FORK` for dynamic coverage.
- **State Inspection:** Reads CPU registers (RDI/RSI) to reconstruct execution state.
- **Enforcement Mechanism:** Manipulates `ORIG_RAX` to enforce policy decisions at the kernel boundary.

### 2. Analysis Layer (Python / Data Space)
*Located in `src/brain.py`*
- **Policy Engine:** A WiSARD-based classifier receiving serialized state signals.
- **Semantic Cortex:** parsing and evaluating string arguments against defined security invariants.

### 3. Orchestration Layer (Bash)
*Located in root*
- **Lifecycle Controller:** `sentinel.sh` manages the initialization and teardown of the IPC bridge.

---

## Research Direction

The project investigates: *Can we enforce semantic security invariants on arbitrary Linux process trees?*

- [x] **M0.9:** IPC Bridge (C-Python Interop).
- [x] **M1.0:** Online Inference Loop.
- [x] **M1.1:** Active Enforcement ("Kill Switch").
- [x] **M1.2:** Semantic Policy Evaluation.
- [x] **M2.0:** Dynamic Process Tree Coverage (Grandchild Scope).
- [ ] **M2.1:** Sequence Analysis (Sliding Window Behavioral Detection).
- [ ] **M3.0:** Full Memory Introspection (Socket Argument Extraction).

---

## Usage (Experimental Platform)

Sentinel M2.0 supports monitoring of direct binaries and wrapper scripts.

### 1. Build the Artifact
```bash
gcc src/main.c -o sentinel
chmod +x sentinel.sh

```

### 2. Execute Control Loop

Syntax: `./sentinel.sh <SYSCALL_KEYWORD> <COMMAND> <ARGS>`

**Experiment A: Safe State**

```bash
./sentinel.sh mkdir mkdir safe_folder

```

*Observation:* `✅ SAFE` (Syscall allowed).

**Experiment B: Malicious State (Recursive)**

```bash
./sentinel.sh rename ./run_ransomware.sh

```

*Observation:* `🚨 POLICY VIOLATION` -> **Blocked** (Sentinel tracks Bash → Python → Rename).

---

*Research Author: Nevin Shine.*

