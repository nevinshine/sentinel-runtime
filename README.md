# Sentinel Runtime

![Stable](https://img.shields.io/badge/stable-v1.1-blue?style=flat-square)
![Beta](https://img.shields.io/badge/release-v1.2_beta-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-active_semantic_defense-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Active Research
> **Stable:** v1.1 (Active Neural Blocking)
> **Current Release:** v1.2-beta (Semantic Platform & Orchestration)

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
| **Platform Orchestration**| v1.2 | ✅ **Stable** | Unified execution via `sentinel.sh`. |

---

## Architecture

Sentinel operates as a closed feedback loop:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/`*
- **Runtime Monitor:** A custom `ptrace` tracer that pauses execution.
- **The Eye:** Reads memory registers (RDI/RSI) to extract file paths and arguments.
- **The Enforcer:** Overwrites `ORIG_RAX` with `-1` to neutralize malicious calls.

### 2. Analysis Layer (Python / Data Space)
*Located in `analysis/`*
- **The Brain:** A **WiSARD (Weightless Neural Network)** that acts as the policy engine.
- **Semantic Cortex:** Analyzes string arguments for context (e.g., preventing access to sensitive paths).

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
- [ ] **v2.0:** Sequence Analysis (Sliding Window Behavioral Detection).

---

## Usage (The Platform)

As of v1.2, you no longer need to manage multiple terminals. The Orchestrator handles everything.

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

**Example: A Malicious Operation**

```bash
./sentinel.sh mkdir mkdir my_malware_folder

```

*Result:* `🚨 MALICIOUS INTENT` -> **Blocked** (`Function not implemented`).

---

*Maintained by Nevin Shine.*
