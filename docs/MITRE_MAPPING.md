# Sentinel Runtime: MITRE ATT&CK Coverage Map

**Version:** M3.3.4
**Date:** 2026-01-26
**Author:** Nevin
**Status:** Active Defense

## Coverage Summary
Sentinel Runtime maps purely to the **Execution**, **Defense Evasion**, and **Exfiltration** tactics of the MITRE ATT&CK Framework.

| ID | Tactic | Technique Name | Sentinel Detection Method |
| :--- | :--- | :--- | :--- |
| **T1048** | Exfiltration | Exfiltration Over Alternative Protocol | **Heuristic State Machine:** Blocks data flow from `SENSITIVE_FILE` → `READ` → `SOCKET`. |
| **T1485** | Impact | Data Destruction | **Semantic Blocking:** Prevents `unlink`/`rm` syscalls on files tagged `SENSITIVE_USER_FILE`. |
| **T1036.005** | Defense Evasion | Masquerading: Match Legitimate Name or Location | **Path Canonicalization:** Resolves Symlinks (`realpath`) to detect aliases pointing to sensitive files (e.g., `game_save.dat` -> `id_rsa`). |
| **T1562.001** | Defense Evasion | Impair Defenses: Disable or Modify Tools | **Watchdog Persistence:** Service automatically respawns if terminated (`SIGTERM`/`SIGKILL`) by an attacker. |
| **T1559** | Execution | Inter-Process Communication | **Taint Tracking:** Tracks sensitive data moving across pipes (`dup`/`dup2`) to detect internal staging before exfiltration. |

---

## Deep Dive: Detection Logic

### 1. Exfiltration (T1048)
* **Attack Vector:** Attacker reads `id_rsa` and attempts to write it to a network socket.
* **Sentinel Logic:**
    * **Trigger:** `open("id_rsa")` sets state `SENSITIVE_FILE_OPENED`.
    * **Taint:** `read()` moves state to `SENSITIVE_DATA_HELD`.
    * **Block:** `connect()` + `write()` triggers `EXFILTRATION_ATTEMPT`.
* **Status:** ✅ **Implemented (M3.2)**

### 2. Data Destruction (T1485)
* **Attack Vector:** Ransomware attempts to delete (`rm`) victim files to force payment.
* **Sentinel Logic:**
    * **Trigger:** `unlinkat()` or `rename()` syscalls.
    * **Context:** Target file matches `SENSITIVE_USER_FILE` regex (e.g., `*.docx`, `protected.txt`).
    * **Block:** Immediate denial of syscall with `EPERM`.
* **Status:** ✅ **Implemented (M3.1)**

### 3. Masquerading (T1036.005)
* **Attack Vector:** Attacker creates a Symlink (`ln -s /etc/shadow /tmp/log`) to bypass path-based rules.
* **Sentinel Logic:**
    * **Resolution:** All paths are passed through `os.path.realpath()` before classification.
    * **Result:** The engine sees `/etc/shadow` regardless of the alias used.
    * **Status:** ✅ **Implemented (M3.3)**

---

## Gaps & Roadmap (Future Work)

| Gap ID | Description | MITRE Mapping | Planned Fix (M4) |
| :--- | :--- | :--- | :--- |
| **G1** | **Memory Injection** | Process Injection (T1055) | Sentinel cannot currently detect if a process modifies another process's memory (`ptrace` abuse). Plan: Add `PTRACE_POKETEXT` hooks. |
| **G2** | **Kernel Rootkits** | Rootkit (T1014) | If attacker loads a kernel module, they can bypass Sentinel. Plan: Migrate logic to eBPF (Ring 0). |
| **G3** | **Encrypted Exfil** | Exfiltration Over Encrypted Channel (T1030) | Sentinel sees the write, but cannot inspect the payload content if the app encrypts it internally before writing. |

---
*Reference: [MITRE ATT&CK Framework](https://attack.mitre.org/)*