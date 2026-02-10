# Sentinel M8: The Bloodline (Inheritance Engine)

**Status:** ✅ RELEASED
**Date:** Feb 9, 2026
**Version:** M8.2 (Robust Inode-Only Enforcement)

## Overview
Sentinel M8 implements the "Bloodline" feature, which ensures that restricted processes cannot evade enforcement by spawning child processes. It also introduces a robust Inode-Only blocking mechanism to solve device ID mismatch issues.

## Core Features

### 1. Inheritance (The Bloodline)
- **Mechanism:** Uses `tp_btf/sched_process_fork` tracepoint.
- **Logic:** When a restricted parent `fork()`s, the child automatically inherits the restriction (`sentinel_policy` map entry).
- **Result:** Beating `exec` by forking first (e.g. `bash -> ping`) is no longer possible.

### 2. Lifecycle Management (GC)
- **Mechanism:** Uses `tp_btf/sched_process_exit` tracepoint.
- **Logic:** When a restricted process dies, its entry is removed from the policy map.
- **Benefit:** Prevents map exhaustion and stale rules.

### 3. Robust Enforcement (Inode-Only)
- **Mechanism:** `lsm/bprm_check_security` hook.
- **Logic:** Checks the file's **Inode Number** against the blocklist.
- **Improvement:** Removed `Device ID` and `Mount Namespace` checks. This eliminates false negatives caused by kernel/userspace device ID mismatches (e.g. `stat` seeing dev 66304 vs kernel seeing `s_dev` 35).

## How to Run

### Manual
1. Build: `make`
2. Run Loader: `sudo ./sentinel_loader`
3. Mark PID: `sudo ./sentinel_loader mark <PID>`

### Automated One-Click Fix
Use the included helper script to kill old instances, rebuild, and reload:
```bash
sudo ./reload_m8.sh
```

## Failure Diagnosis (Fixed)
- **Symptom:** Ping blocked in map but executing successfully.
- **Cause:** `stat.st_dev` (userspace) != `super_block.s_dev` (kernel).
- **Fix:** Switched to unique Inode-only matching.
