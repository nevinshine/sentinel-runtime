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

    printf("[SENTINEL] 🟢 Starting Runtime Verification Engine v0.6...\n");

    child_pid = fork();

    if (child_pid == 0) {
        // --- CHILD (The Subject) ---
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        
        // Execute the Iron Shell (launcher)
        // Ensure ./launcher exists in the same folder!
        char *args[] = {"./launcher", NULL};
        execvp(args[0], args);
        
        // Fallback if launcher is missing
        perror("[CHILD] Exec failed");
        exit(1);

    } else {
        // --- PARENT (The Sentinel) ---
        int status;
        struct user_regs_struct regs;
        
        waitpid(child_pid, &status, 0); // Wait for exec start
        ptrace(PTRACE_SYSCALL, child_pid, 0, 0); // Start tracing

        while(1) {
            waitpid(child_pid, &status, 0);
            if (WIFEXITED(status)) break;

            // Get CPU State
            ptrace(PTRACE_GETREGS, child_pid, NULL, &regs);

            // --- INTERCEPTION LOGIC ---

            // 1. DETECT WRITE (Printing to screen)
            // RDI = FD (1 is stdout), RSI = String Address, RDX = Length
            if (regs.orig_rax == 1 && regs.rdi == 1) {
                char *text = read_string(child_pid, regs.rsi);
                
                printf("\n[SENTINEL] 👁️  INTERCEPTED OUTPUT:\n");
                printf("    ├── Source:    Syscall::WRITE (1)\n");
                printf("    ├── Length:    %llu bytes\n", regs.rdx);
                printf("    └── Payload:   \"%s\"\n", text);
                
                free(text);
            }

            // 2. DETECT FILE OPEN (Accessing disk)
            // RSI = File Path Address for OPENAT (257)
            if (regs.orig_rax == 257) {
                char *path = read_string(child_pid, regs.rsi);
                
                printf("\n[SENTINEL] 📂 INTERCEPTED FILE ACCESS:\n");
                printf("    ├── Source:    Syscall::OPENAT (257)\n");
                printf("    └── Target:    \"%s\"\n", path);
                
                free(path);
            }

            // Resume
            ptrace(PTRACE_SYSCALL, child_pid, 0, 0);
        }
        printf("[SENTINEL] 🔴 Subject exited. Surveillance complete.\n");
    }

    return 0;
}
