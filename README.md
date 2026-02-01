# Sentinel Runtime Defense System
> **Unified Host-Based Intrusion Detection & Network Defense System (HIDS/NIDS)**

```console
root@Sentinel-Node:~# ./sentinel_guard --attach --persistence

 [ INIT ] CHECKING PTRACE SCOPE ........................ [YAMA: OFF]
 [ IPC  ] OPENING LOGIC BRIDGE ......................... [/tmp/sentinel_req]
 [ LOAD ] LOADING SEMANTIC MAPS ........................ [DONE]
 [ W-DOG] STARTING WATCHDOG ORCHESTRATOR ............... [ACTIVE]
 [ HOOK ] ATTACHING INTERCEPTOR ........................ [PID: ALL]

   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝

  >> UNIFIED RUNTIME DEFENSE GRID (v3.6) <<

  [RUNTIME STATUS]
  > VERSION:       M3.6 (Unified Grid: Auto-DLP + Logic Trap)
  > ENGINE:        C (Ptrace Sysemulation)
  > BRAIN:         Python (Deterministic State Machine)
  > FIREWALL:      Hyperion XDP (Bridge Active)
  > TARGET:        Research Artifact (CISPA / Saarland MSc)

```

---

## [ 0x01 ] ABSTRACT

**Sentinel Runtime** is a deterministic runtime defense system that unifies **Host-Based Security** (Syscall Analysis) with **Network Defense** (XDP Firewall).

Unlike traditional systems that rely on probabilistic AI or static signatures, Sentinel uses a **Semantic State Machine** to track the "Kill Chain" of a process in real-time. By connecting the syscall layer to the network layer, Sentinel achieves **Autonomous Data Loss Prevention (Auto-DLP)**: detecting sensitive file access in userspace and instantly reprogramming the kernel-level firewall to block exfiltration.

> **[Read the MITRE Mapping](https://github.com/nevinshine/sentinel-runtime/blob/main/docs/MITRE_MAPPING.md)** - A technical deep-dive into how Sentinel aligns with the ATT&CK framework.

---

## [ 0x02 ] 🎥 LIVE DEMOS (DUAL-PERSPECTIVE)

We provide two perspectives of the system in action to validate both the **internal engineering logic** and the **external security efficacy**.

### 1. The Engineer's View: "The Watchtower"

*A view inside the Logic Brain (`brain.py`). Observe the real-time interception of syscalls, state transitions (IDLE -> SENSITIVE_HELD), and the instant "BLOCK" decision upon exfiltration attempts.*

[![asciicast](https://asciinema.org/a/8cmVyWWx4JjpTnam.svg)](https://asciinema.org/a/8cmVyWWx4JjpTnam)

### 2. The Validator's View: "The Scoreboard"

*The automated `unified_test_suite.sh` proving the system passes 4/4 critical security challenges: Trust Filter, Integrity Shield, USB Trap, and Auto-DLP.*

[![asciicast](https://asciinema.org/a/0Pmewo1HxjA4tXFo.svg)](https://asciinema.org/a/0Pmewo1HxjA4tXFo)

---

## [ 0x03 ] ARCHITECTURAL PIVOT: WHY LOGIC > AI?

In earlier iterations (v1.0 - v2.0), Sentinel employed a **"Deep Wise Network" (DWN)** based on PyTorch/TensorFlow for anomaly detection. In **Milestone 3.6**, we architecturally pivoted to a **Deterministic State Machine**.

| Feature | Legacy AI Model (DWN) | Modern Logic Brain (M3.6) |
| --- | --- | --- |
| **Decision Basis** | Probabilistic (0.0 - 1.0 score) | Deterministic (State Transitions) |
| **False Positives** | High (Unpredictable behavior) | **Zero** (For defined Kill Chains) |
| **Explainability** | "Black Box" (Why did it block?) | **Audit Trail** (Read Secret -> Write Socket) |
| **Performance** | Heavy (Requires GPU/High CPU) | **Lightweight** (Pure Python Logic) |
| **Reaction Time** | ~200ms (Inference Latency) | **<10ms** (Instant State Check) |

**Conclusion:** For runtime enforcement, certainty is superior to probability. The State Machine ensures we never block a legitimate process unless it strictly violates a defined security policy (e.g., Ransomware behavior).

---

## [ 0x04 ] CAPABILITY MILESTONES

| FEATURE | MILESTONE | STATUS | DESCRIPTION |
| --- | --- | --- | --- |
| **Exfiltration Detection** | M3.1 | ✅ | State Machine + Cross-Process Taint Tracking. |
| **Path Canonicalization** | M3.3 | ✅ | Defeats Symlink/Traversal evasion via `realpath`. |
| **Watchdog Persistence** | M3.4 | ✅ | Self-healing orchestrator for tamper resistance. |
| **Integrity Shield** | M3.5 | ✅ | **[NEW]** Anti-Ransomware (Blocks `unlink`/`rename` on sensitive files). |
| **Auto-DLP Bridge** | M3.6 | ✅ | **[NEW]** Connects Host Events to Network Firewall (Hyperion XDP). |

---

## [ 0x05 ] USAGE (M3.6 UNIFIED MODE)

### 1. Build The Engine

```bash
make clean && make

```

### 2. Start The Defense Grid

You must run the Brain (Logic) and the Body (Interceptor) together.

**Terminal 1: The Brain**

```bash
python3 src/analysis/brain.py

```

**Terminal 2: The Body (or Test Suite)**

```bash
# Run the validation suite
./tests/unified_test_suite.sh

```

---

## [ 0x06 ] TECHNICAL SPECIFICATIONS (M3.6)

### The "Auto-DLP" Bridge

Sentinel M3.6 introduces a novel bridge between userspace and kernelspace.

1. **Trigger:** User opens `top_secret.pdf`.
2. **Analysis:** Brain tags file as `SENSITIVE_USER_FILE`.
3. **Action:** Brain writes the filename to `signatures.txt`.
4. **Enforcement:** Hyperion XDP (Network Firewall) reads the signature and instantly drops any outgoing packet containing that filename.

### Performance Profile

* **Syscall Overhead:** ~25x (Optimized `ptrace` handling).
* **Memory Footprint:** <45MB (Reduced by 60% after removing AI dependencies).
* **Stability:** Non-blocking I/O ensures the host system never freezes, even if the Brain is paused.

---

## [ 0x07 ] CITATION

```text
@software{sentinel2026,
  author = {Nevin},
  title = {Sentinel: Unified Runtime Defense via Semantic State Machine},
  year = {2026},
  version = {V3.6.0},
  url = {[https://github.com/nevinshine/sentinel-runtime](https://github.com/nevinshine/sentinel-runtime)}
}