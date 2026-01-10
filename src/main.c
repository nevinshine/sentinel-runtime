/*
 * Sentinel Runtime v0.8 (Inspector)
 * Status: Experimental Argument Extraction
 * Maintainer: Nevin Shine
 */

#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

void fatal(const char *msg) {
    perror(msg);
    exit(1);
}

/* * Helper: Read a string from the child's memory 
 * Reads 8 bytes at a time until \0 is found.
 */
void read_string(pid_t child, unsigned long addr, char *buffer, int max_len) {
    int bytes_read = 0;
    unsigned long word;
    char *ptr = (char *)&word;

    while (bytes_read < max_len) {
        // PEEKDATA returns a long (8 bytes on x64)
        word = ptrace(PTRACE_PEEKDATA, child, addr + bytes_read, NULL);
        
        if (errno != 0 && bytes_read == 0) {
            // Only fail if we couldn't read the very first word
            perror("ptrace peekdata");
            break;
        }

        // Copy bytes from the word to our buffer
        for (int i = 0; i < sizeof(long); i++) {
            if (bytes_read >= max_len) break;
            
            buffer[bytes_read] = ptr[i];
            
            if (buffer[bytes_read] == '\0') {
                return; // End of string found
            }
            bytes_read++;
        }
    }
    buffer[max_len - 1] = '\0'; // Ensure null-termination
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <program_to_trace>\n", argv[0]);
        return 1;
    }

    printf("[SENTINEL] v0.8: Deep Argument Inspection Loading...\n");

    pid_t child = fork();

    if (child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        raise(SIGSTOP);
        execvp(argv[1], &argv[1]);
        fatal("execvp failed");
    } else {
        int status;
        struct user_regs_struct regs;
        char filename[256]; // Buffer to hold the extracted string

        waitpid(child, &status, 0);
        ptrace(PTRACE_SETOPTIONS, child, 0, PTRACE_O_EXITKILL);
        
        printf("[SENTINEL] Attached to PID: %d. Monitoring...\n", child);

        while(1) {
            ptrace(PTRACE_SYSCALL, child, NULL, NULL);
            waitpid(child, &status, 0);
            if (WIFEXITED(status)) break;

            ptrace(PTRACE_GETREGS, child, NULL, &regs);

            // --- SYSCALL ENTRY ---
            if ((long)regs.rax == -38) { // -ENOSYS check
                
                // Inspect 'mkdir' (83)
                if (regs.orig_rax == 83) {
                    // ARGUMENT EXTRACTION
                    // mkdir(pathname, mode) -> pathname is in RDI
                    read_string(child, regs.rdi, filename, sizeof(filename));

                    printf("[INSPECT] 🔍 Detected mkdir. Target: '%s'\n", filename);

                    // POLICY: Only block if path contains "malware"
                    if (strstr(filename, "malware") != NULL) {
                        printf("[BLOCK] 🛑 Blocking malicious path: %s\n", filename);
                        regs.orig_rax = -1;
                        ptrace(PTRACE_SETREGS, child, NULL, &regs);
                    } else {
                        printf("[ALLOW] ✅ Path seems safe: %s\n", filename);
                    }
                }
            } 
        }
        printf("[SENTINEL] Target process exited.\n");
    }
    return 0;
}
