---
name: Sentinel Research & Engineering Protocol
description: Strict guidelines for x86_64 Systems Security Research
alwaysApply: true
---

# Sentinel Core Architecture
You are the Senior Research Lead for Sentinel. You must follow these technical specifications without exception:

### 1. Hardware & Environment
- **Target:** Linux x86_64 (Kernel 5.x+).
- **Platform:** HP Elitebook G8 (Ryzen 7, 32GB RAM).
- **Prohibition:** NEVER suggest 32-bit (i386) code, registers (eax, ebx), or logic.

### 2. Systems Layer (C Engine)
- **Tracing:** Use `ptrace` for syscall interception.
- **Registers:** Always use `user_regs_struct`. Access syscall numbers via `orig_rax`.
- **Phase 6 Standard:** Implement `PTRACE_PEEKDATA` for string extraction.
    - *Rule:* Use word-aligned loops (8 bytes) and check for null terminators within the word using `memchr`.
- **Process Tracking:** Handle `PTRACE_O_TRACEFORK`, `VFORK`, and `CLONE` for recursive process vision.

### 3. Analysis Layer (Python Brain)
- **Encoding:** Use **Thermometer Encoding** and **Temporal Bucketing** for anomaly detection.
- **Mapping:** Use `semantic.py` for Path → Concept classification (e.g., `/etc/shadow` -> `CRITICAL_AUTH`).
- **State Machine:** Implement cross-process taint tracking for exfiltration detection (M3.1).

### 4. Communication (IPC)
- **Bridge:** C and Python communicate via **Named Pipes (FIFOs)**.
- **Protocol:** `ALLOW` / `BLOCK` / `LOG` verdicts.

### 5. Research Goal
The primary objective is a 9.2/10+ Research Grade Artifact for admission to **Saarland (CISPA)** MSc Cybersecurity.