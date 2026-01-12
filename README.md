# Sentinel Runtime

![Stable](https://img.shields.io/badge/stable-v0.8-blue?style=flat-square)
![Experimental](https://img.shields.io/badge/experimental-v0.9-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-ipc_&_neural_link-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Active Research
> **Stable:** v0.8 (Deep Introspection & Argument Reading)
> **Experimental:** v0.9 (IPC Neural Bridge)

## Abstract

**Sentinel Runtime** is a lightweight Linux runtime security system designed to observe, analyze, and intervene in program behavior at execution time.

Unlike traditional AVs, Sentinel intercepts Linux system calls using `ptrace` to establish a semantic understanding of process intent. It connects a high-speed C interception engine to a Python-based Weightless Neural Network (DWN) for real-time decision making.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## Capability Status

| Feature | Version | Status | Description |
| :--- | :--- | :--- | :--- |
| **Runtime Tracing** | v0.6 | ✅ **Stable** | Reliable interception of syscalls (`ptrace` entry/exit). |
| **Policy Enforcement** | v0.7 | ✅ **Stable** | Active blocking via register rewriting. TOCTOU-safe. |
| **Deep Introspection** | v0.8 | ✅ **Stable** | Argument extraction (reading strings via `PTRACE_PEEKDATA`). |
| **IPC Neural Bridge** | v0.9 | ⚠️ **Experimental** | **The Link.** High-speed Named Pipe (`/tmp/sentinel_ipc`) connecting C to Python. |

---

## Architecture

Sentinel operates as a hybrid system:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/`*
- **Runtime Monitor:** A custom `ptrace`-based tracer.
- **Deep Inspector:** Uses `PTRACE_PEEKDATA` to read memory (filenames, args).
- **Transmitter (v0.9):** Streams syscall events to the Python Brain via IPC pipes.

### 2. Analysis Layer (Python / Data Space)
*Located in `analysis/`*
- **The Bridge:** A listener that reads raw syscall streams from the C engine.
- **The Brain:** A **Differentiable Weightless Neural Network (DWN)** that classifies behavior as "Benign" or "Malicious."

---

## Roadmap & Research Direction

The project investigates: *Can we build a programmable immune system for Linux processes?*

- [x] **v0.6:** Deep Runtime Introspection (Argument Extraction).
- [x] **v0.7:** Policy Enforcement (Stable Blocking).
- [x] **v0.8:** Semantic Awareness (Reading Filenames).
- [~] **v0.9:** IPC Bridge (Connecting C Engine to Python Brain).
- [ ] **v1.0:** Live Neural Defense (Full Integration).

---

## Usage (Quick Start)

### 1. Start the Brain (Listener)
The Python bridge must be running first to create the pipe.
```bash
python3 analysis/bridge.py

```

### 2. Run the Sentinel (Engine)

In a separate terminal:

```bash
gcc src/main.c -o sentinel
./sentinel mkdir test_folder

```

*Expected Output:* The Brain terminal should receive: `SYSCALL:mkdir:test_folder`

---

*Maintained by Nevin Shine.*

