/*
 * Sentinel Runtime v0.7.1 (Sync-Fix)
 * Status: Experimental Policy Enforcement
 * Maintainer: Nevin Shine
 */

#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

void fatal(const char *msg) {
    perror(msg);
    exit(1);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <program_to_trace>\n", argv[0]);
        return 1;
    }

    printf("[SENTINEL] v0.7.1: Active Policy Engine (Auto-Sync) Loading...\n");

    pid_t child = fork();

    if (child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        raise(SIGSTOP);
        execvp(argv[1], &argv[1]);
        fatal("execvp failed");
    } else {
        int status;
        struct user_regs_struct regs;

        waitpid(child, &status, 0);
        ptrace(PTRACE_SETOPTIONS, child, 0, PTRACE_O_EXITKILL);
        
        printf("[SENTINEL] Attached to PID: %d. Monitoring...\n", child);

        while(1) {
            ptrace(PTRACE_SYSCALL, child, NULL, NULL);
            waitpid(child, &status, 0);
            if (WIFEXITED(status)) break;

            ptrace(PTRACE_GETREGS, child, NULL, &regs);

            // --- SYNCHRONIZATION CHECK ---
            // On x86_64, RAX is -ENOSYS (-38) on Entry.
            // If it's -38, we are BEFORE execution. If not, we are AFTER.
            if ((long)regs.rax == -38) {
                
                /* === SYSCALL ENTRY (WE CAN BLOCK HERE) === */
                
                if (regs.orig_rax == 83) { // mkdir
                    printf("[BLOCK] 🛑 Malicious syscall ENTRY detected: mkdir (83)\n");
                    
                    // NEUTRALIZE: Set to -1
                    regs.orig_rax = -1;
                    ptrace(PTRACE_SETREGS, child, NULL, &regs);
                    
                    printf("[BLOCK] ⚡ Neutralized (converted to -1)\n");
                }

            } else {
                /* === SYSCALL EXIT (TOO LATE) === */
                // Debug: Did the block work? 
                // If blocked, result should be -38 (-ENOSYS). If 0, we failed.
                if (regs.orig_rax == 83) {
                     printf("[AUDIT] mkdir finished. Kernel returned: %lld\n", (long long)regs.rax);
                }
            }
        }
        printf("[SENTINEL] Target process exited.\n");
    }
    return 0;
}
