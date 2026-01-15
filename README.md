# Sentinel Runtime

![Stable](https://img.shields.io/badge/stable-v1.2-blue?style=flat-square)
![Release](https://img.shields.io/badge/release-v2.0_process_tree-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-behavioral_edr_kernel-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Active Research
> **Stable:** v1.2 (Semantic Intelligence)
> **Current Release:** v2.0 (Dynamic Process Tree Defense)

## Abstract

**Sentinel Runtime** is a lightweight Linux runtime security system designed to observe, analyze, and intervene in program behavior at execution time.

Unlike traditional AVs, Sentinel intercepts Linux system calls using `ptrace` to establish a semantic understanding of process intent. It operates as a cybernetic loop, connecting a high-speed C interception engine to a Python-based Weightless Neural Network (WiSARD) for real-time decision making.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## Capability Status

| Feature | Version | Status | Description |
| :--- | :--- | :--- | :--- |
| **Deep Introspection** | v0.8 | ✅ **Stable** | Argument extraction (reading strings via `PTRACE_PEEKDATA`). |
| **Live Neural Defense** | v1.0 | ✅ **Stable** | Real-time inference loop (<1ms latency). |
| **Active Blocking** | v1.1 | ✅ **Stable** | **The Kill Switch.** Injecting `ENOSYS` to block syscalls based on AI verdict. |
| **Semantic Intelligence**| v1.2 | ✅ **Stable** | Context-aware blocking (e.g., allow `mkdir`, block `mkdir malware`). |
| **Process Tree Defense** | v2.0 | ✅ **New** | **Recursive Fork Tracking.** Monitors entire process trees (Shell → Python → Ransomware) via `PTRACE_O_TRACEFORK`. |

---

## Architecture

Sentinel operates as a closed feedback loop:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/`*
- **Runtime Monitor:** A recursive `ptrace` engine that auto-attaches to child processes.
- **Event Loop:** Handles asynchronous signals (`PTRACE_EVENT_FORK`) to track dynamic execution flows.
- **The Enforcer:** Overwrites `ORIG_RAX` with `-1` to neutralize malicious calls instantly.

### 2. Analysis Layer (Python / Data Space)
*Located in `src/brain.py`*
- **The Brain:** A policy engine that receives live signals from the C kernel.
- **Semantic Cortex:** Analyzes file paths and arguments for context (e.g., blocking `rename` operations in protected zones).

### 3. Orchestration Layer (Bash)
*Located in root*
- **The Commander:** `sentinel.sh` manages the lifecycle of the Brain and Body, ensuring clean startup and teardown.

---

## Roadmap & Research Direction

The project investigates: *Can we build a programmable immune system for Linux processes?*

- [x] **v0.9:** IPC Bridge (Connecting C Engine to Python Brain).
- [x] **v1.0:** Live Neural Defense (Inference Loop).
- [x] **v1.1:** Active Blocking (The "Kill Switch").
- [x] **v1.2:** Semantic Awareness & Orchestration.
- [x] **v2.0:** Dynamic Process Tree Monitoring (Handling "Grandchild" processes).
- [ ] **v2.1:** Sequence Analysis (Sliding Window Behavioral Detection).
- [ ] **v3.0:** Full Memory Introspection (Argument Extraction for Network Sockets).

---

## Usage (The Platform)

Sentinel v2.0 can monitor direct binaries or wrapper scripts (like Bash launching Python).

### 1. Build the Engine
```bash
gcc src/main.c -o sentinel
chmod +x sentinel.sh

```

### 2. Run the Platform

Syntax: `./sentinel.sh <SYSCALL_KEYWORD> <COMMAND> <ARGS>`

**Example: A Safe Operation**

```bash
./sentinel.sh mkdir mkdir safe_folder

```

*Result:* `✅ SAFE` (Folder created).

**Example: A Malicious Script (Recursive Monitoring)**

```bash
./sentinel.sh rename ./run_ransomware.sh

```

*Result:* `🚨 MALICIOUS INTENT` -> **Blocked** (Sentinel tracks Bash → Python → Rename Syscall).

---

*Maintained by Nevin Shine.*
