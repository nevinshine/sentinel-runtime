# Sentinel Runtime: Host-Based Active Defense

> *  **Status:** Research Artifact (Active)
> * **Current Capability:** M3.4 (Persistence + MITRE Mapping + Canonicalization)
> * **Target:** CISPA / Saarland MSc Application
> * **[Read the MITRE Mapping](https://www.google.com/search?q=docs/MITRE_MAPPING.md)** - A technical deep-dive into how Sentinel aligns with the ATT&CK framework.

## Abstract

**Sentinel Runtime** is a Linux host-based defense system focused on syscall-level monitoring and cross-process taint tracking. By establishing a closed-loop control system via `ptrace`, Sentinel connects a high-speed C interception engine to a Python-based **Cognitive Engine** to enforce security policies in real-time.

---

## Research Proof (Video Artifacts)

These recordings provide immutable proof of the system's defensive capabilities:

* **`sentinel_demo.cast`**: Active blocking of Ransomware-style file destruction (`unlink`).
* **`sentinel_evasion.cast`**: Detection of sophisticated exfiltration using **Symlink Aliasing** and **FD Duplication**.
* **`sentinel_persistence.cast`**: Demonstration of the **M3.4 Watchdog** resurrecting the security stack after a `SIGKILL` attack.

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
./bin/watchdog.sh

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

*Research Author: Nevin Shine, Systems Security Research Engineer.*