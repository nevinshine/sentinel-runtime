# Sentinel Runtime

> **Status:** Active Research (v0.7 – Policy Enforcement)  
> **Focus:** Linux Runtime Verification, Syscall Interception, Active Defense  
> **Maintainer:** Nevin Shine (Systems Security Research Engineer)

## Abstract

Sentinel Runtime is a lightweight Linux runtime security system designed to observe, analyze, and intervene in program behavior at execution time. Instead of relying on static signatures or binary inspection, Sentinel intercepts Linux system calls using `ptrace` to establish a semantic understanding of process intent. The system actively enforces security policies by blocking malicious system calls (e.g., unauthorized file access) in real-time before they execute.

---

## Architecture

Sentinel is intentionally split into two distinct layers to separate mechanism from policy:

### 1. Systems Layer (C / Kernel Space)
Located in `src/`.
- **Runtime Monitor:** A custom `ptrace`-based tracer.
- **Deep Introspection:** Uses `PTRACE_PEEKDATA` to extract syscall arguments (strings, file paths) from the child process's virtual memory.
- **Active Policy Engine:** Intercepts critical syscalls (`openat`, `execve`) and neutralizes malicious requests by rewriting CPU registers (`orig_rax = -1`) in real-time.

### 2. Analysis Layer (Python / Data Space)
Located in `analysis/` and `models/`.
- **Bridge:** Converts raw syscall streams into fixed-length behavioral vectors (Thermometer Encoding).
- **Brain:** A **Differentiable Weightless Neural Network (DWN)** that learns normal execution paths.
- **Inference:** Uses strictly defined look-up tables (LUTs) for low-latency, CPU-only anomaly scoring.

---

## Current Capabilities (v0.7)

- **Process Control:** Full lifecycle management (fork/exec/wait) of child processes.
- **Syscall Tracing:** Real-time interception of syscall numbers (identity).
- **Memory Teleportation:** Extraction of raw string arguments (e.g., file paths) from the child's memory space.
- **Active Blocking:** Ability to cancel specific syscalls based on content (e.g., blocking access to `/etc/passwd`) while keeping the process alive.

---

## Roadmap & Research Direction

The project investigates: *Can we build a programmable immune system for Linux processes?*

- [x] **v0.5:** Anomaly Engine (Numbers & sequences).
- [x] **v0.6:** Memory Extraction (Deep argument inspection via `PTRACE_PEEKDATA`).
- [x] **v0.7:** Policy Enforcement (Real-time blocking of malicious syscalls).
- [ ] **v0.8:** Online Anomaly Scoring (Connecting the Python Brain to the C Body).

---

## Usage (Quick Start)

### 1. Compile the Sentinel (Guard)
```bash
gcc src/main.c -o sentinel_v0.7

```

### 2. Compile the Target (Simulation)

```bash
gcc launcher.c -o launcher

```

### 3. Run Active Defense

```bash
./sentinel_v0.7

```

---

## 🛠️ Tech Stack

* **Core Engine:** C (Linux API, ptrace, waitpid)
* **Analysis:** Python 3.10+, PyTorch (Custom Autograd)
* **Target OS:** Linux x86_64 (Tested on Ubuntu 24.04 Kernel 6.8)

---

## 📚 References

* **ptrace(2) man page** – Linux Programmer's Manual
* **DWN:** Bacellar et al., *"Differentiable Weightless Neural Networks"*, ICML 2024
* **ULEEN:** Susskind et al., *"Ultra-Low-Energy Edge Neural Networks"*, TACO 2023

---

*Built by [Nevin Shine](https://www.linkedin.com/in/nevin-shine-b403b932b/) — Systems Security Research Engineer.*
