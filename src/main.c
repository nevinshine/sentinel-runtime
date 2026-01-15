#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>

#define PIPE_REQ "/tmp/sentinel_req"
#define PIPE_RESP "/tmp/sentinel_resp"

// --- Helper to read string from ANY child memory ---
void read_string(pid_t pid, unsigned long addr, char *str, int max_len) {
    int len = 0;
    unsigned long word;
    while (len < max_len) {
        word = ptrace(PTRACE_PEEKDATA, pid, addr + len, NULL);
        if (errno != 0) break;
        memcpy(str + len, &word, sizeof(word));
        if (memchr(&word, 0, sizeof(word)) != NULL) break;
        len += sizeof(word);
    }
    str[max_len - 1] = '\0';
}

int get_verdict(int fd_read) {
    char buf[2];
    int n = read(fd_read, buf, 1);
    if (n > 0 && buf[0] == '0') return 0; // Block
    return 1; // Allow
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <syscall_name> <program> [args...]\n", argv[0]);
        return 1;
    }

    pid_t original_child = fork();
    if (original_child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        raise(SIGSTOP); // Wait for parent to set options
        execvp(argv[2], &argv[2]);
        perror("execvp");
        exit(1);
    } else {
        int status;
        struct user_regs_struct regs;
        int fd_req = open(PIPE_REQ, O_WRONLY);
        int fd_resp = open(PIPE_RESP, O_RDONLY);
        
        setvbuf(stdout, NULL, _IONBF, 0);
        printf("[SENTINEL v2] 🌲 Process Tree Monitoring Active.\n");

        // 1. Wait for child to stop initially
        waitpid(original_child, &status, 0);

        // 2. ENABLE FORK TRACING (The Magic Line)
        ptrace(PTRACE_SETOPTIONS, original_child, 0, 
               PTRACE_O_TRACEFORK | PTRACE_O_TRACEEXEC | PTRACE_O_EXITKILL);

        // Resume the first child
        ptrace(PTRACE_SYSCALL, original_child, NULL, NULL);

        while (1) {
            // 3. WAIT FOR ANY PID (-1)
            pid_t current_pid = waitpid(-1, &status, __WALL);
            if (current_pid == -1) break; // No children left

            if (WIFEXITED(status) || WIFSIGNALED(status)) {
                if (current_pid == original_child) break; // Main shell died
                continue; // Some sub-process died, keep going
            }

            // 4. CHECK FOR EVENTS (New Process Created)
            if ((status >> 16) == PTRACE_EVENT_FORK) {
                // A new child was born! Auto-attached.
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
                continue;
            }

            // If stopped by a syscall
            if (WIFSTOPPED(status) && WSTOPSIG(status) == SIGTRAP) {
                ptrace(PTRACE_GETREGS, current_pid, NULL, &regs);

                char path[256] = {0};
                char *verb = NULL;
                int detected = 0;
                unsigned long addr_to_read = 0;

                // --- SYSCALL LOGIC ---
                if (regs.orig_rax == 83) { verb = "mkdir"; addr_to_read = regs.rdi; detected = 1; } 
                else if (regs.orig_rax == 258) { verb = "mkdir"; addr_to_read = regs.rsi; detected = 1; }
                else if (regs.orig_rax == 82) { verb = "rename"; addr_to_read = regs.rdi; detected = 1; }
                else if (regs.orig_rax == 264 || regs.orig_rax == 316) { 
                    verb = "rename"; addr_to_read = regs.rsi; detected = 1; 
                }

                if (detected) {
                    read_string(current_pid, addr_to_read, path, 256);
                    char msg[512];
                    sprintf(msg, "SYSCALL:%s:%s\n", verb, path);
                    write(fd_req, msg, strlen(msg));
                    
                    if (!get_verdict(fd_resp)) {
                        printf("[SENTINEL] 🛡️ BLOCKED PID %d: %s('%s')\n", current_pid, verb, path);
                        regs.orig_rax = -1;
                        ptrace(PTRACE_SETREGS, current_pid, NULL, &regs);
                    }
                }
                // Resume THIS specific PID
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            } else {
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            }
        }
        close(fd_req); close(fd_resp);
    }
    return 0;
}
