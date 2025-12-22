# 🛡️ Sentinel Sandbox

> **Status:** Active Research (v0.1 – Kernel Baseline)  
> **Focus:** Linux Kernel Security, Syscall Analysis, Weightless ML, MLSecOps  
> **Maintainer:** Nevin Shine  

---

## 🔍 Overview

**Sentinel Sandbox** is a lightweight, **ptrace-based Linux runtime analysis system** designed to detect anomalous and potentially malicious program behavior through **system call behavior modeling**.

Unlike traditional sandboxes that rely on heavy virtualization (e.g., Cuckoo, VMware), Sentinel operates **directly on the host kernel**, intercepting system calls in real time with minimal overhead.

### 🎯 Research Goal

To investigate the effectiveness of **Differentiable Weightless Neural Networks (DWN)** for detecting **zero-day behavioral anomalies** in Linux binaries using **raw syscall traces**, under **CPU-only and resource-constrained environments**.

---

## 🏗️ System Architecture

Sentinel operates as a three-layer research system:

1. **The Interceptor (C / Kernel Space)**  
   A custom `ptrace`-based tracer that halts process execution at syscall **entry points** and records syscall numbers (`orig_rax`) with strict semantic correctness.

2. **The Bridge (Python / Data Interface)**  
   A deterministic transformation pipeline that converts syscall streams into fixed-length **binary representations** using:
   - Sliding windows
   - Bag-of-syscalls histograms
   - Thermometer encoding (Hamming-distance preserving)

3. **The Brain (Python / PyTorch)**  
   A custom **Differentiable Weightless Neural Network (DWN)** trained using **Extended Finite Difference (EFD)**, enabling gradient-based learning over discrete lookup tables while preserving logic-based inference.

---

## 🧠 Machine Learning Core

- **Architecture:** Multi-discriminator Weightless Neural Network (WiSARD / ULEEN style)
- **Training:** Differentiable via Extended Finite Difference (EFD)
- **Inference:** Pure lookup-table based (no matrix multiplication)
- **Execution:** CPU-only, no GPU dependency

This design allows Sentinel to combine:
- interpretability
- low latency
- hardware realizability
- kernel-level behavioral fidelity

---

## 🗺️ Research Roadmap

- [x] **Phase 1: Loader & Process Control**  
  Process creation, PID control, syscall interception setup

- [x] **Phase 2: Kernel Tracing**  
  Accurate syscall entry tracing using `ptrace` (`orig_rax`, entry-only logging)

- [x] **Phase 3: Data Representation Bridge**  
  Sliding windows, histogram aggregation, thermometer encoding

- [x] **Phase 4: DWN Integration**  
  ICML-level EFD-based Differentiable Weightless Neural Network

- [ ] **Phase 5: Anomaly Scoring & Detection**  
  Normal-only training, abnormal trace scoring, thresholding

- [ ] **Phase 6: Evaluation & Ablation Studies**  
  Window size, encoding resolution, baseline comparisons

---

## 🛠️ Tech Stack

- **Languages:** C (Kernel Tracing), Python (ML & Data Pipeline)
- **Kernel APIs:** `ptrace`, `waitpid`, `user_regs_struct`
- **ML Architecture:** Differentiable Weightless Neural Networks (DWN)
- **Training Framework:** PyTorch (custom autograd)
- **OS:** Ubuntu 24.04 LTS (Hardened Kernel)

---

## 📚 Key References

This work is grounded in the following research:

- **ULEEN:**  
  Susskind et al., *"ULEEN: A Novel Architecture for Ultra-Low-Energy Edge Neural Networks"*, TACO 2023

- **DWN:**  
  Bacellar et al., *"Differentiable Weightless Neural Networks"*, ICML 2024

- **LogicNets:**  
  Nag et al., *"LogicNets vs. ULEEN: Comparing Two Novel High-Throughput Edge ML Inference Techniques"*, MWSCAS

---

## 📌 Notes

- Runtime syscall logs (`sentinel_log.csv`) are **generated at execution time** and are intentionally excluded from version control.
- The project prioritizes **semantic correctness and research reproducibility** over production hardening.

---

*Built by [Nevin Shine](https://www.linkedin.com/in/nevin-shine-b403b932b/) — Independent Researcher, Systems Security.*
