# Sentinel Runtime

![Milestone](https://img.shields.io/badge/milestone-M2.0_Recursive_Tracking-blue?style=flat-square&logo=linux)
![Architecture](https://img.shields.io/badge/architecture-research_modular-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-systems_security_research-363636?style=flat-square)

> **Status:** Research Artifact (Active)
> **Current Capability:** M2.0 (Recursive Process Tree Tracking)
> **Target:** CISPA / Saarland MSc Application

## Abstract

**Sentinel Runtime** is a Linux runtime defense system designed to investigate syscall-level observability and semantic enforcement.

Unlike traditional signature-based AVs, Sentinel leverages `ptrace` to establish a closed-loop runtime control system. It connects a high-speed C interception kernel to a Python-based analysis engine (WiSARD) to evaluate process intent against security policies in real-time.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## ⚡ M2.0: Recursive Process Tracking (Live Demo)

Demonstration of **Sentinel Runtime** intercepting a multi-stage fork evasion attempt. 
The engine tracks the process tree across generations (`Parent` -> `Dropper` -> `Payload`) using `PTRACE_O_TRACEFORK` logic to eliminate the "Grandchild Blind Spot."

![Sentinel M2.0 Demo](assets/sentinel_demo.gif)

**Trace Log Analysis:**
* **PID 67840 (Yellow):** Level 1 Dropper detected.
* **PID 67841 (Magenta):** Level 2 Grandchild intercepted recursively.
* **Verdict:** Syscall `mkdir("RANSOMWARE_ROOT")` blocked in real-time.

---

## Capability Milestone Status

| Feature | Milestone | Status | Description |
| :--- | :--- | :--- | :--- |
| **Deep Introspection** | M0.8 | ✅ **Validated** | Argument extraction via `PTRACE_PEEKDATA`. |
| **Online Inference Loop** | M1.0 | ✅ **Validated** | Real-time decision pipeline via Named Pipes (IPC). |
| **Active Blocking** | M1.1 | ✅ **Validated** | **Enforcement Semantics.** Injecting `ENOSYS` to neutralize malicious syscalls. |
| **Process Tree Tracking** | M2.0 | ✅ **Operational** | **Recursive Fork Monitoring.** Tracing dynamic trees via `PTRACE_O_TRACEFORK`. |
| **Semantic Extraction** | M3.0 | 🚧 **In Progress** | Universal argument mapping for `connect`, `unlink`, `execve`. |

---

## Architecture (Refactored M2.0)

Sentinel operates as a modular closed-loop runtime control system:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/engine/`*
- **Interception Engine (`main.c`):** A recursive `ptrace` monitor that handles `PTRACE_EVENT_FORK` / `CLONE`.
- **Visualization (`logger.c`):** Real-time tree hierarchy rendering for research logging.
- **Enforcement:** Manipulates `ORIG_RAX` to enforce policy decisions at the kernel boundary.

### 2. Analysis Layer (Python / Data Space)
*Located in `src/analysis/`*
- **Policy Engine:** Receives serialized state signals (`SYSCALL:mkdir:args`).
- **Verdict Issuer:** Returns binary Block/Allow decisions to the kernel.

### 3. Test Vectors
*Located in `tests/evasion/`*
- **Recursive Fork Bomb:** Simulates "dropper" malware behavior to stress-test the recursive tracking.

---

## Usage

Sentinel M2.0 uses a standard `make` build system.

### 1. Build the Artifact
```bash
make
# Compiles ./bin/sentinel and ./bin/recursive_fork

```

### 2. Execute Control Loop

You must run the Analysis Engine (Brain) and the Kernel Interceptor (Sentinel) simultaneously.

**Terminal 1 (The Brain):**

```bash
python3 src/analysis/mock_brain.py

```

**Terminal 2 (The Sentinel):**

```bash
# Syntax: ./bin/sentinel <trigger_word> <target_binary>
./bin/sentinel run ./bin/recursive_fork

```

---

*Research Author: Nevin Shine.*
