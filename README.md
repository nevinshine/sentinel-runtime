# Sentinel Runtime: Host-Based Active Defense

> * **Status:** Research Artifact (Final)
> * **Current Capability:** M3.4 (Persistence + MITRE Mapping + Canonicalization)
> * **Target:** CISPA / Saarland MSc Application
> * **[Read the MITRE Mapping](docs/MITRE_MAPPING.md)** - A technical deep-dive into how Sentinel aligns with the ATT&CK framework.

## Abstract

**Sentinel Runtime** is a Linux host-based defense system focused on syscall-level monitoring and cross-process taint tracking. By establishing a closed-loop control system via `ptrace`, Sentinel connects a high-speed C interception engine to a Python-based **Cognitive Engine** to enforce security policies in real-time.

---

## Research Proof (Video Artifacts)

These recordings provide immutable proof of the system's defensive capabilities.

### 1. Ransomware Blocking (M3.0)
*Active blocking of Ransomware-style file destruction (`unlink`).*

![Ransomware Blocking](assets/sentinel_demo.gif)

### 2. Evasion Detection (M3.3 - Symlink & FD Duplication)
*Detection of sophisticated exfiltration using **Symlink Aliasing** and **FD Duplication**.*

![Evasion Demo](assets/sentinel_evasion.gif)

### 3. Watchdog Persistence (M3.4 - Self-Healing)
*Demonstration of the **Watchdog Orchestrator** resurrecting the security stack after a `SIGKILL` attack.*

![Persistence Demo](assets/sentinel_persistence.gif)

---

## Capability Milestone Status

| Feature | Milestone | Status | Description |
| --- | --- | --- | --- |
| **Exfiltration Detection** | M3.1 | ✅ | State Machine + Cross-Process Taint Tracking. |
| **Benchmark Suite** | M3.2 | ✅ | Quantified syscall overhead and IPC throughput. |
| **Path Canonicalization** | M3.3 | ✅ | **[NEW]** Defeats Symlink/Traversal evasion via `realpath` resolution. |
| **Watchdog Persistence** | M3.4 | ✅ | **[NEW]** Self-healing orchestrator for tamper resistance (T1562.001). |
| **MITRE Alignment** | M3.4 | ✅ | **[NEW]** Formal mapping to 5+ ATT&CK techniques. |

---

## Performance Benchmarks (M3.2)

| Metric | Value |
| --- | --- |
| **Syscall Overhead** | 20-40x (ptrace-based) |
| **IPC Throughput** | 28,628 ops/sec |
| **Memory Usage** | ~100 MB total |

---

## Usage (M3.4 Service Mode)

### 1. Build

```bash
make clean && make
```

### 2. Start Persistent Guardian

To run Sentinel in a self-healing "Service Mode" that resists termination:

```bash
./scripts/watchdog.sh
```

### 3. Verify Evasion Block

```bash
# In a separate terminal
sudo ./bin/sentinel test ./bin/dup_test
```

---

## Tags & Versioning

| Tag | Milestone | Key Achievement |
| --- | --- | --- |
| **M3.2** | Benchmarks | Performance baseline established. |
| **M3.3** | Hardening | Path Canonicalization implemented. |
| **M3.4** | Persistence | Watchdog Orchestrator & MITRE Mapping finalized. |

---

*Research Author: Nevin Shine, Systems Security Research Engineer.*
