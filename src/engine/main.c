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
#include "logger.h" 

#define PIPE_REQ "/tmp/sentinel_req"
#define PIPE_RESP "/tmp/sentinel_resp"
#define MAX_PIDS 4194304 // Covers modern Linux /proc/sys/kernel/pid_max
#define COLOR_RED     "\033[1;31m"
#define COLOR_RESET   "\033[0m"

// Global depth map for process tree context
int pid_depths[MAX_PIDS] = {0}; 

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
    memset(pid_depths, 0, sizeof(pid_depths));

    pid_t original_child = fork();
    if (original_child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        raise(SIGSTOP); 
        execvp(argv[2], &argv[2]);
        perror("execvp");
        exit(1);
    } else {
        int status;
        struct user_regs_struct regs;
        
        int fd_req = open(PIPE_REQ, O_WRONLY);
        if (fd_req < 0) { 
            fprintf(stderr, "Error: Start the Python analyzer first! (Pipe not found)\n"); 
            return 1; 
        }
        int fd_resp = open(PIPE_RESP, O_RDONLY);
        
        setvbuf(stdout, NULL, _IONBF, 0);
        
        // 1. Attach to Root
        waitpid(original_child, &status, 0);
        pid_depths[original_child] = 0;
        log_tree_event(original_child, getpid(), 0, "INIT", NULL);

        // 2. Set Options (The Core of M2.0)
        ptrace(PTRACE_SETOPTIONS, original_child, 0, 
               PTRACE_O_TRACEFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC | PTRACE_O_EXITKILL);

        ptrace(PTRACE_SYSCALL, original_child, NULL, NULL);

        while (1) {
            pid_t current_pid = waitpid(-1, &status, __WALL);
            if (current_pid == -1) break;

            if (WIFEXITED(status) || WIFSIGNALED(status)) {
                if (current_pid == original_child) break;
                continue;
            }

            // 3. Handle Process Spawning (Recursive Tracking)
            if ((status >> 16) == PTRACE_EVENT_FORK || (status >> 16) == PTRACE_EVENT_CLONE) {
                unsigned long new_pid_l;
                ptrace(PTRACE_GETEVENTMSG, current_pid, 0, &new_pid_l);
                pid_t new_pid = (pid_t)new_pid_l;
                
                // Inherit depth + 1
                pid_depths[new_pid] = pid_depths[current_pid] + 1;
                
                log_tree_event(new_pid, current_pid, pid_depths[new_pid], "SPAWNED", "Fork Detected");
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
                continue;
            }

            // 4. Handle Syscalls
            if (WIFSTOPPED(status) && WSTOPSIG(status) == SIGTRAP) {
                ptrace(PTRACE_GETREGS, current_pid, NULL, &regs);
                char path[256] = {0};
                char *verb = NULL;
                int detected = 0;
                unsigned long addr_to_read = 0;

                // Simple Syscall Map (To be upgraded in Phase 6)
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
                    
                    // FIXED: Handle write error to silence compiler warning
                    if (write(fd_req, msg, strlen(msg)) == -1) {
                        // If pipe is broken, just continue (or handle fatal error)
                    }
                    
                    if (!get_verdict(fd_resp)) {
                        printf("      " COLOR_RED "[BLOCKED]" COLOR_RESET " PID: %d | Action: %s | Target: %s\n", current_pid, verb, path);
                        regs.orig_rax = -1; // Invalidate syscall
                        ptrace(PTRACE_SETREGS, current_pid, NULL, &regs);
                    }
                }
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            } else {
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            }
        }
        close(fd_req); close(fd_resp);
    }
    return 0;
}
