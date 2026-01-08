#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <unistd.h>

// --- MEMORY EXTRACTION ENGINE (The "Teleporter") ---

// Helper: Read a string from the child's memory
// Input: Child PID, Address in Child's Virtual Memory
// Output: Heap-allocated string (YOU MUST FREE THIS)
char *read_string(pid_t child, unsigned long long addr) {
    int allocated = 64;
    int read_bytes = 0;
    char *val = malloc(allocated);
    unsigned long long tmp;

    while (1) {
        // 1. Expand buffer if needed
        if (read_bytes + sizeof(tmp) > allocated) {
            allocated *= 2;
            val = realloc(val, allocated);
        }

        // 2. PEEKDATA: Read 8 bytes (one word) from child
        errno = 0;
        tmp = ptrace(PTRACE_PEEKDATA, child, addr + read_bytes, NULL);
        
        if (errno != 0) {
            val[read_bytes] = 0; // Terminate on error
            break;
        }

        // 3. Copy bytes to our buffer
        memcpy(val + read_bytes, &tmp, sizeof(tmp));

        // 4. Scan for NULL terminator
        int done = 0;
        for (int i = 0; i < sizeof(tmp); i++) {
            if (val[read_bytes + i] == 0) {
                done = 1;
                break;
            }
        }
        
        read_bytes += sizeof(tmp);
        if (done) break;
    }
    return val;
}

// --- MAIN SENTINEL LOGIC ---

int main(int argc, char *argv[]) {
    pid_t child_pid;
    printf("[SENTINEL] 🛡️  Phase 7: Active Policy Enforcement Engine\n");

    child_pid = fork();

    if (child_pid == 0) {
        // --- CHILD (The Victim) ---
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        
        // Ensure ./launcher exists in the root folder!
        char *args[] = {"./launcher", NULL};
        execvp(args[0], args);
        
        perror("[CHILD] Exec failed");
        exit(1);

    } else {
        // --- PARENT (The Guard) ---
        int status;
        struct user_regs_struct regs;
        
        waitpid(child_pid, &status, 0); // Wait for exec start
        ptrace(PTRACE_SETOPTIONS, child_pid, 0, PTRACE_O_TRACESYSGOOD);

        while(1) {
            // 1. Wait for Syscall ENTRY
            ptrace(PTRACE_SYSCALL, child_pid, 0, 0);
            waitpid(child_pid, &status, 0);
            if (WIFEXITED(status)) break;

            // 2. Get CPU State
            ptrace(PTRACE_GETREGS, child_pid, NULL, &regs);

            // 3. CHECK POLICY: Is this an OPENAT (257) or OPEN (2)?
            // Note: Modern Linux mostly uses openat (257).
            if (regs.orig_rax == 257) {
                // RSI holds the address of the file path string
                char *path = read_string(child_pid, regs.rsi);
                
                // --- THE BLOCKING LOGIC ---
                // If they touch "/etc/passwd", we kill the request.
                if (strstr(path, "passwd") != NULL) {
                    
                    printf("\n[SENTINEL] 🚫 BLOCKED MALICIOUS ACCESS!\n");
                    printf("    ├── Target:  \"%s\"\n", path);
                    printf("    └── Action:  SYSCALL CANCELLED (-1)\n");

                    // 🛑 THE JEDI MIND TRICK 🛑
                    // We set the syscall number to -1 so the kernel ignores it.
                    regs.orig_rax = -1; 
                    ptrace(PTRACE_SETREGS, child_pid, NULL, &regs);
                
                } else {
                    // Allowed files (like libraries)
                    printf("[SENTINEL] ✅ ALLOWED: \"%s\"\n", path);
                }
                free(path);
            }

            // 4. Wait for Syscall EXIT
            // We must step over the exit, even if we cancelled it, to stay in sync.
            ptrace(PTRACE_SYSCALL, child_pid, 0, 0);
            waitpid(child_pid, &status, 0);
            if (WIFEXITED(status)) break;
        }
        printf("[SENTINEL] 🔴 Subject exited. Surveillance complete.\n");
    }

    return 0;
}
