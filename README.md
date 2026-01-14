# Sentinel Runtime

![Stable](https://img.shields.io/badge/stable-v0.9-blue?style=flat-square)
![Alpha](https://img.shields.io/badge/release-v1.0_alpha-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-live_neural_defense-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Active Research
> **Stable:** v0.9 (IPC Neural Bridge)
> **Current Release:** v1.0-alpha (Live Neural Inference)

## Abstract

**Sentinel Runtime** is a lightweight Linux runtime security system designed to observe, analyze, and intervene in program behavior at execution time.

Unlike traditional AVs, Sentinel intercepts Linux system calls using `ptrace` to establish a semantic understanding of process intent. It connects a high-speed C interception engine to a Python-based Weightless Neural Network (DWN) for real-time decision making.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## Capability Status

| Feature | Version | Status | Description |
| :--- | :--- | :--- | :--- |
| **Policy Enforcement** | v0.7 | ✅ **Stable** | Active blocking via register rewriting. TOCTOU-safe. |
| **Deep Introspection** | v0.8 | ✅ **Stable** | Argument extraction (reading strings via `PTRACE_PEEKDATA`). |
| **IPC Neural Bridge** | v0.9 | ✅ **Stable** | High-speed Named Pipe (`/tmp/sentinel_ipc`) connecting C to Python. |
| **Live Neural Defense** | v1.0 | ⚠️ **Alpha** | **The Brain.** Real-time inference using WiSARD (Allow/Block verdicts). |

---

## Architecture

Sentinel operates as a cybernetic loop:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/`*
- **Runtime Monitor:** A custom `ptrace` tracer that pauses execution.
- **Deep Inspector:** Extracts syscall arguments (e.g., filenames) from memory.
- **Transmitter:** Streams telemetry to the Analysis Layer via IPC.

### 2. Analysis Layer (Python / Data Space)
*Located in `analysis/`*
- **The Bridge:** A listener that receives the raw syscall stream.
- **The Brain:** A **WiSARD (Weightless Neural Network)** that receives the signal, checks its memory, and returns a verdict (`BENIGN` or `ANOMALY`) in <1ms.

---

## Roadmap & Research Direction

The project investigates: *Can we build a programmable immune system for Linux processes?*

- [x] **v0.8:** Semantic Awareness (Reading Filenames).
- [x] **v0.9:** IPC Bridge (Connecting C Engine to Python Brain).
- [x] **v1.0-alpha:** Live Neural Defense (First successful inference loop).
- [ ] **v1.1:** Full Feedback Loop (Python triggers the Block in C).

---

## Usage (Quick Start)

### 1. Start the Brain (Listener)
The Python bridge must be running first to create the neural link.
```bash
python3 analysis/bridge.py

```

*Status:* `[BRIDGE] Listening on /tmp/sentinel_ipc...`

### 2. Run the Sentinel (Engine)

In a separate terminal:

```bash
gcc src/main.c -o sentinel
./sentinel mkdir test_folder

```

### 3. Observe the Verdict

The Brain terminal will output the real-time decision:

> `🟢 ALLOW | mkdir (test_folder) -> ✅ BENIGN`

---

*Maintained by Nevin Shine.*

