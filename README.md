# Sentinel Runtime

![Stable](https://img.shields.io/badge/stable-v0.7-blue?style=flat-square)
![Experimental](https://img.shields.io/badge/experimental-v0.8-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-linux_kernel_&_ptrace-363636?style=flat-square&logo=linux&logoColor=white)

> **Status:** Active Research
> **Stable:** v0.7 (Policy Enforcement & TOCTOU Safety)
> **Experimental:** v0.8 (Semantic Deep Inspection)

## Abstract

**Sentinel Runtime** is a lightweight Linux runtime security system designed to observe, analyze, and intervene in program behavior at execution time.

Unlike traditional AVs, Sentinel intercepts Linux system calls using `ptrace` to establish a semantic understanding of process intent. It can read syscall arguments (like file paths) in real-time and block malicious actions before the kernel executes them.

🔗 **Research Dossier:** [nevinshine.github.io/runtime-security-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## Capability Status

| Feature | Version | Status | Description |
| :--- | :--- | :--- | :--- |
| **Runtime Tracing** | v0.6 | ✅ **Stable** | Reliable interception of syscalls (`ptrace` entry/exit). |
| **Policy Enforcement** | v0.7 | ✅ **Stable** | Active blocking via register rewriting (`orig_rax = -1`). TOCTOU-safe. |
| **Deep Introspection** | v0.8 | ⚠️ **Experimental** | **Semantic Blocking.** Content-aware filtering (reading child memory strings). |
| **Anomaly Scoring** | v0.9 | 🚧 **Planned** | Online integration with DWN Neural Network. |

---

## Architecture

Sentinel is intentionally split into two distinct layers:

### 1. Systems Layer (C / Kernel Space)
*Located in \`src/\`*
- **Runtime Monitor:** A custom \`ptrace\`-based tracer.
- **Deep Introspection:** Uses \`PTRACE_PEEKDATA\` to extract syscall arguments (strings, file paths) from the child's virtual memory.
- **Active Policy Engine:** Neutralizes malicious requests. *v0.7 stabilized the blocking mechanics; v0.8 adds content awareness.*

### 2. Analysis Layer (Python / Data Space)
*Located in \`analysis/\`*
- **Bridge:** Converts raw syscall streams into fixed-length behavioral vectors.
- **Brain:** A **Differentiable Weightless Neural Network (DWN)**.

---

## Roadmap & Research Direction

The project investigates: *Can we build a programmable immune system for Linux processes?*

- [x] **v0.5:** Anomaly Engine (Numbers & sequences).
- [x] **v0.6:** Deep Runtime Introspection (Argument Extraction).
- [x] **v0.7:** Policy Enforcement (Stable Blocking & Race Condition Fixes).
- [~] **v0.8:** Semantic Blocking (Content-Aware Filtering).
- [ ] **v0.9:** Online Anomaly Scoring.

---

## 🚀 Usage (Quick Start)

### 1. Compile the Sentinel
```bash
gcc src/main.c -o sentinel
```

### 2. Run Semantic Defense
Sentinel will run `mkdir`. It will **allow** "safe_folder" but **block** "malware_folder".

```bash
# Test 1: Should Succeed
./sentinel mkdir safe_folder

# Test 2: Should be Blocked
./sentinel mkdir malware_folder
```

---
*Maintained by Nevin Shine.*

