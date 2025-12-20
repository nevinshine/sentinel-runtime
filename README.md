# 🛡️ Sentinel Sandbox

> **Status:** Active Research (v0.1)  
> **Focus:** Linux Kernel, ptrace, Syscall Analysis, MLSecOps  
> **Maintainer:** Nevin Shine

## 📜 Overview
**Sentinel Sandbox** is a lightweight, custom-built runtime analysis environment designed to detect malicious behavior in Linux binaries. Unlike traditional sandboxes that rely on heavy virtualization (Cuckoo/VMware), Sentinel uses the Linux `ptrace` API to intercept system calls in real-time with minimal overhead.

**Research Goal:** To investigate the efficacy of modeling raw system call traces as **Time-Series Sequences vs. Control Flow Graphs (CFG)** for detecting zero-day anomalies using Unsupervised Learning (Isolation Forests).

## 🏗️ Architecture (Planned)
The system operates on three distinct layers:
1.  **The Interceptor (C/Kernel):** A custom tracer using `ptrace` to halt process execution at specific syscall entry/exit points.
2.  **The Cage (Docker):** An isolated container environment where the untrusted binary executes.
3.  **The Brain (Python/ML):** An anomaly detection engine that consumes the syscall log stream to flag deviations from baseline behavior.

## 🗺️ Roadmap
- [ ] **Phase 1: The Loader** (Process instantiation, memory mapping, & PID control)
- [ ] **Phase 2: The Tracer** (Intercepting `execve`, `open`, `write` syscalls)
- [ ] **Phase 3: The Logger** (Structured logging of register states & arguments)
- [ ] **Phase 4: ML Integration** (Training Isolation Forest on benign process traces)

## 🛠️ Tech Stack
* **Language:** C (Core Logic), Python (Data Analysis)
* **Kernel APIs:** `ptrace`, `waitpid`, `user_regs_struct`
* **Tools:** Docker, Make, GDB
* **OS:** Ubuntu 24.04 LTS

---
*Built by [Nevin Shine](https://www.linkedin.com/in/nevin-shine-b403b932b/) - Junior Researcher, Systems Security.*
