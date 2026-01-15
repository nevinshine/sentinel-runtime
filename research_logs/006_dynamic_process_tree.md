# Research Log 006: Dynamic Process Tree Instrumentation
**Date:** 2026-01-15
**Project:** Sentinel Sandbox (Phase 6a)
**Author:** Nevin, Systems Security Research Mentor
**Topic:** Overcoming ptrace Blind Spots via PTRACE_O_TRACEFORK

### 1. The Research Problem: The "Grandchild" Blind Spot
In v1.0, Sentinel used a direct parent-child attachment model. This failed when monitoring shells (like `bash`) because standard `ptrace` does not propagate to child processes. The "Grandchild" process (the ransomware) executed outside the tracer's scope.

### 2. Engineering Solution: Recursive Process Tracking
We implemented `ptrace(PTRACE_SETOPTIONS, ...)` with the `PTRACE_O_TRACEFORK` flag.
* **Mechanism:** This forces the Linux kernel to automatically attach Sentinel to any new process spawned by the tracee.
* **Event Loop:** The control loop was updated to `waitpid(-1)` to handle signals from any process in the tree, distinguishing between the Shell (Parent) and the Payload (Grandchild).

### 3. Implementation Evidence
The updated C engine (v2.0) successfully intercepted a multi-stage execution flow:
* **Parent:** bash (PID 33408) -> Traced
* **Event:** PTRACE_EVENT_FORK detected
* **Child:** python3 (PID 33409) -> Auto-attached
* **Interception:** `rename("data/money.csv")` called by the child.
* **Verdict:** BLOCKED by Policy.

### 4. Significance
This milestone transitions Sentinel from a simple "Syscall Interceptor" to a true **Behavioral EDR (Endpoint Detection & Response)** kernel capable of tracking process lineages.
