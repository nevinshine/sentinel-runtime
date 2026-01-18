# Sentinel Runtime

![Milestone](https://img.shields.io/badge/milestone-M2.1_Universal_Defense-blue?style=flat-square&logo=linux)
![Architecture](https://img.shields.io/badge/architecture-research_modular-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-systems_security_research-363636?style=flat-square)

> **Status:** Research Artifact (Active)
> **Current Capability:** M2.1 (Universal Syscall Extraction & VFORK Tracking)
> **Target:** CISPA / Saarland MSc Application

## Abstract

**Sentinel Runtime** is a Linux runtime defense system designed to investigate syscall-level observability and semantic enforcement.

Unlike traditional signature-based AVs, Sentinel leverages `ptrace` to establish a closed-loop runtime control system. It connects a high-speed C interception kernel to a Python-based analysis engine (WiSARD) to evaluate process intent against security policies in real-time.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## M2.1: Universal Active Defense (Live Demo)

Demonstration of **Sentinel Runtime** operating in "X-Ray Mode." It actively tracks modern shell behavior (`vfork`) and enforces a **Block-on-Intent** policy.

**Scenario:** A user attempts to delete a protected file (`unlink` syscall).
**Result:** Sentinel intercepts the syscall, consults the Policy Engine, and injects a block verdict (`EPERM`) before the kernel executes the deletion.

*(Place your new GIF here showing the 'rm' block)*

---

## Capability Milestone Status

| Feature | Milestone | Status | Description |
| :--- | :--- | :--- | :--- |
| **Deep Introspection** | M0.8 | ✅ **Validated** | Argument extraction via `PTRACE_PEEKDATA`. |
| **Online Inference Loop** | M1.0 | ✅ **Validated** | Real-time decision pipeline via Named Pipes (IPC). |
| **Recursive Process Tracking** | M2.0 | ✅ **Validated** | Tracing dynamic trees via `PTRACE_O_TRACEFORK`. |
| **Universal Extraction** | M2.1 | ✅ **Operational** | **The Universal Eye.** Map-based extraction for `unlink`, `openat`, `execve`. |
| **Stealth Tracking** | M2.1 | ✅ **Operational** | **VFORK Support.** Detecting optimized shell spawns (`dash`/`sh`). |
| **Semantic Bucketing** | M3.0 | 🚧 **In Progress** | Converting raw paths into semantic concepts (e.g., "Ransomware Activity"). |

---

## Architecture (Refactored M2.1)

Sentinel operates as a modular closed-loop runtime control system:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/engine/`*
- **Interception Engine (`main.c`):** A recursive `ptrace` monitor supporting `FORK`, `CLONE`, and `VFORK`.
- **Universal Map (`syscall_map.h`):** A research artifact defining the "DNA" of syscalls (Registers, Types, Names).
- **Visualization (`logger.c`):** Real-time tree hierarchy rendering.

### 2. Analysis Layer (Python / Data Space)
*Located in `src/analysis/`*
- **Neural Engine (`brain.py`):** The decision center. Parses `SYSCALL:verb:arg` signals and issues Block/Allow verdicts.
- **Mock Brain (`mock_brain.py`):** Lightweight testing tool for engine validation.

### 3. Test Vectors
*Located in `tests/`*
- **Adversarial Scenarios:** Standard Linux utilities (`rm`, `ls`) are used to test real-world evasion resilience.

---

## Usage

Sentinel M2.1 uses a standard `make` build system.

### 1. Build the Artifact
```bash
make clean && make
# Compiles ./bin/sentinel

```

### 2. Execute Control Loop

You must run the Analysis Engine (Brain) and the Kernel Interceptor (Sentinel) simultaneously.

**Terminal 1 (The Brain):**

```bash
python3 src/analysis/brain.py
# Displays: [INFO] Neural Engine Online.

```

**Terminal 2 (The Sentinel):**

```bash
# Syntax: ./bin/sentinel <trigger_word> <target_binary>
sudo ./bin/sentinel test /bin/sh

# Inside the monitored session:
# touch protected.txt
# rm protected.txt  <-- BLOCKED

```

---

*Research Author: Nevin Shine.*


