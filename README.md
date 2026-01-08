# Sentinel Runtime

![Stable](https://img.shields.io/badge/stable-v0.6-blue?style=flat-square)
![Experimental](https://img.shields.io/badge/experimental-v0.7-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-linux_kernel_&_ptrace-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Active Research
> **Stable:** v0.6 (Deep Runtime Introspection)
> **Experimental:** v0.7 (Policy Enforcement)

## Abstract

**Sentinel Runtime** is a lightweight Linux runtime security system designed to observe, analyze, and intervene in program behavior at execution time.

Instead of relying on static signatures, Sentinel intercepts Linux system calls using `ptrace` to establish a semantic understanding of process intent.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## Capability Status

| Feature | Version | Status | Description |
| :--- | :--- | :--- | :--- |
| **Runtime Tracing** | v0.6 | ✅ **Stable** | Reliable interception of syscalls (`ptrace` entry/exit). |
| **Deep Introspection** | v0.6 | ✅ **Stable** | Argument extraction (reading strings from child memory). |
| **Policy Enforcement** | v0.7 | ⚠️ **Experimental** | Active blocking via register rewriting (`orig_rax = -1`). |
| **Anomaly Scoring** | v0.8 | 🚧 **Planned** | Online integration with DWN Neural Network. |

---

## Architecture

Sentinel is intentionally split into two distinct layers:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/`*
- **Runtime Monitor:** A custom `ptrace`-based tracer.
- **Deep Introspection:** Uses `PTRACE_PEEKDATA` to extract syscall arguments (strings, file paths).
- **Active Policy Engine:** Neutralizes malicious requests. *Current experimental focus: verifying errno correctness and restart semantics.*

### 2. Analysis Layer (Python / Data Space)
*Located in `analysis/`*
- **Bridge:** Converts raw syscall streams into fixed-length behavioral vectors.
- **Brain:** A **Differentiable Weightless Neural Network (DWN)**.

---

## Roadmap & Research Direction

The project investigates: *Can we build a programmable immune system for Linux processes?*

- [x] **v0.5:** Anomaly Engine (Numbers & sequences).
- [x] **v0.6:** Deep Runtime Introspection (Argument Extraction).
- [~] **v0.7:** Policy Enforcement (**Experimental** - Hardening enforcement invariants).
- [ ] **v0.8:** Online Anomaly Scoring.

---

## Usage (Quick Start)

### 1. Compile the Sentinel
```bash
gcc src/main.c -o sentinel

```

### 2. Compile the Target

```bash
gcc launcher.c -o launcher

```

### 3. Run Active Defense (Experimental)

```bash
./sentinel

```

---

*Maintained by Nevin Shine.*

