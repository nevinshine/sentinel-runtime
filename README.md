```console
root@Sentinel-Node:~# ./sentinel_guard --attach --persistence

 [ INIT ] CHECKING PTRACE SCOPE ........................ [YAMA: OFF]
 [ IPC  ] OPENING NEURAL BRIDGE ........................ [/tmp/sentinel_req]
 [ LOAD ] LOADING SEMANTIC MAPS ........................ [DONE]
 [ W-DOG] STARTING WATCHDOG ORCHESTRATOR ............... [ACTIVE]
 [ HOOK ] ATTACHING INTERCEPTOR ........................ [PID: ALL]

   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝

  >> HOST-BASED INTRUSION PREVENTION SYSTEM (HIPS) <<

  [RUNTIME STATUS]
  > VERSION:       M3.4 (Persistence + Canonicalization)
  > ENGINE:        C (Ptrace Sysemulation)
  > BRAIN:         Python (Semantic State Machine)
  > TARGET:        Research Artifact (CISPA / Saarland MSc)
  > MITRE:         T1562.001 (Impair Defenses) Mapped

```

---

## [ 0x01 ] ABSTRACT

**Sentinel Runtime** is a Linux host-based defense system focused on syscall-level monitoring and cross-process taint tracking. By establishing a closed-loop control system via `ptrace`, Sentinel connects a high-speed C interception engine to a Python-based **Cognitive Engine** to enforce security policies in real-time.

> **[Read the MITRE Mapping](https://www.google.com/search?q=docs/MITRE_MAPPING.md)** - A technical deep-dive into how Sentinel aligns with the ATT&CK framework.

---

## [ 0x02 ] RESEARCH PROOF (VIDEO ARTIFACTS)

These recordings provide immutable proof of the system's defensive capabilities.

### 1. Ransomware Blocking (M3.0)

*Active blocking of Ransomware-style file destruction (`unlink`).*

![Ransomware Blocking](assets/sentinel_demo.gif)

### 2. Evasion Detection (M3.3)

*Detection of sophisticated exfiltration using **Symlink Aliasing** and **FD Duplication**.*

![Evasion Demo](assets/sentinel_evasion.gif)

### 3. Watchdog Persistence (M3.4)

*Demonstration of the **Watchdog Orchestrator** resurrecting the security stack after a `SIGKILL` attack (Self-Healing).*

---

## [ 0x03 ] CAPABILITY MILESTONES

| FEATURE | MILESTONE | STATUS | DESCRIPTION |
| --- | --- | --- | --- |
| **Exfiltration Detection** | M3.1 | ✅ | State Machine + Cross-Process Taint Tracking. |
| **Benchmark Suite** | M3.2 | ✅ | Quantified syscall overhead and IPC throughput. |
| **Path Canonicalization** | M3.3 | ✅ | **[NEW]** Defeats Symlink/Traversal evasion via `realpath`. |
| **Watchdog Persistence** | M3.4 | ✅ | **[NEW]** Self-healing orchestrator for tamper resistance. |
| **MITRE Alignment** | M3.4 | ✅ | **[NEW]** Formal mapping to 5+ ATT&CK techniques. |

---

## [ 0x04 ] PERFORMANCE BENCHMARKS (M3.2)

| METRIC | VALUE | CONTEXT |
| --- | --- | --- |
| **Syscall Overhead** | 20-40x | Inherent to `ptrace` context switching. |
| **IPC Throughput** | 28,628 ops/sec | Synchronous blocking over named pipes. |
| **Memory Usage** | ~100 MB | Total stack (Engine + Brain + Maps). |

---

## [ 0x05 ] USAGE (M3.4 SERVICE MODE)

### 1. Build Artifacts

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

## [ 0x06 ] TAGS & VERSIONING

| TAG | MILESTONE | KEY ACHIEVEMENT |
| --- | --- | --- |
| **M3.2** | Benchmarks | Performance baseline established. |
| **M3.3** | Hardening | Path Canonicalization implemented. |
| **M3.4** | Persistence | Watchdog Orchestrator & MITRE Mapping finalized. |

---

## [ 0x07 ] CITATION

```text
@software{sentinel2026,
  author = {Nevin},
  title = {Sentinel: Semantic Runtime Defense via Ptrace},
  year = {2026},
  url = {[https://github.com/nevinshine/sentinel-runtime](https://github.com/nevinshine/sentinel-runtime)}
}
```
---

<div align="center">
<sub>Research Author: Nevin Shine, Undergraduate Systems Security Researcher.</sub>
</div>
