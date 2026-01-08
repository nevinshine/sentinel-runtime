# Sentinel Runtime

> **Status:** Active Research (v0.5 – Anomaly Engine)  
> **Focus:** Linux Runtime Verification, Syscall Interception, Behavioral Anomaly Detection  
> **Maintainer:** Nevin Shine (Systems Security Research Engineer)

## Abstract

Sentinel Runtime is a lightweight Linux runtime security system designed to observe and analyze program behavior at execution time. Instead of relying on static signatures or binary inspection, Sentinel intercepts Linux system calls using `ptrace` and models their behavior to detect anomalous or malicious execution patterns. The project explores how syscall-level observability can provide a reliable ground truth for security analysis, even in the presence of obfuscation or AI-generated malware.

---

## Architecture

Sentinel is intentionally split into two distinct layers to separate mechanism from policy:

### 1. Systems Layer (C / Kernel Space)
Located in `src/`.
- **Runtime Monitor:** A custom `ptrace`-based tracer.
- **Interception:** Halts process execution at syscall entry/exit points.
- **Introspection:** Extracts syscall numbers (`orig_rax`) and CPU register states (`RDI`, `RSI`, `RDX`) directly from the kernel struct `user_regs_struct`.

### 2. Analysis Layer (Python / Data Space)
Located in `analysis/` and `models/`.
- **Bridge:** Converts raw syscall streams into fixed-length behavioral vectors (Thermometer Encoding).
- **Brain:** A **Differentiable Weightless Neural Network (DWN)** that learns normal execution paths.
- **Inference:** Uses strictly defined look-up tables (LUTs) for low-latency, CPU-only anomaly scoring.

---

## Current Capabilities (v0.5)

- **Process Control:** Full lifecycle management (fork/exec/wait) of child processes.
- **Syscall Tracing:** Real-time interception of syscall numbers (identity).
- **Register Decoding:** Extraction of raw register values (arguments).
- **Behavioral Modeling:** Offline training of anomaly detectors using Isolation Forests and DWNs.

---

## Roadmap & Research Direction

The project investigates: *What is the minimum observability required to reliably detect intent?*

- **v0.5 (Current):** Anomaly Engine (Numbers & sequences).
- **v0.6 (Next):** Memory Extraction (Deep argument inspection via `PTRACE_PEEKDATA`).
- **v0.7:** Online Anomaly Scoring (Real-time blocking).
- **v0.8:** Policy Enforcement (Preventing specific syscalls).

---

## Tech Stack

- **Core Engine:** C (Linux API, ptrace, waitpid)
- **Analysis:** Python 3.10+, PyTorch (Custom Autograd)
- **Target OS:** Linux x86_64 (Tested on Ubuntu 24.04 Kernel 6.8)

---

## References

- **ptrace(2) man page** – Linux Programmer's Manual
- **DWN:** Bacellar et al., *"Differentiable Weightless Neural Networks"*, ICML 2024
- **ULEEN:** Susskind et al., *"Ultra-Low-Energy Edge Neural Networks"*, TACO 2023

---

*Built by [Nevin Shine](https://www.linkedin.com/in/nevin-shine-b403b932b/) — Systems Security Research Engineer.*
