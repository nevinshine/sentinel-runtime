// src/main.c (Patched for mkdirat)
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

// --- Helper to read string from child memory ---
void read_string(pid_t child, unsigned long addr, char *str, int max_len) {
    int len = 0;
    unsigned long word;
    while (len < max_len) {
        word = ptrace(PTRACE_PEEKDATA, child, addr + len, NULL);
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

    pid_t child = fork();
    if (child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        execvp(argv[2], &argv[2]);
        perror("execvp");
        exit(1);
    } else {
        int status;
        struct user_regs_struct regs;
        int fd_req = open(PIPE_REQ, O_WRONLY);
        int fd_resp = open(PIPE_RESP, O_RDONLY);
        
        // Disable output buffering to ensure logs appear immediately
        setvbuf(stdout, NULL, _IONBF, 0);

        printf("[SENTINEL] 🔗 Connected. Monitoring strict policies.\n");

        while (1) {
            waitpid(child, &status, 0);
            if (WIFEXITED(status)) break;

            ptrace(PTRACE_GETREGS, child, NULL, &regs);

            char path[256] = {0};
            int detected = 0;

            // --- DETECT BOTH SYSCALLS ---
            if (regs.orig_rax == 83) { 
                // mkdir(path) -> Path is in RDI
                read_string(child, regs.rdi, path, 256);
                detected = 1;
            } 
            else if (regs.orig_rax == 258) { 
                // mkdirat(dirfd, path) -> Path is in RSI
                read_string(child, regs.rsi, path, 256);
                detected = 1;
            }

            if (detected) {
                // 1. Send to Brain
                char msg[512];
                sprintf(msg, "SYSCALL:mkdir:%s\n", path);
                write(fd_req, msg, strlen(msg));
                
                // 2. Wait for Verdict
                if (!get_verdict(fd_resp)) {
                    printf("[SENTINEL] 🛡️ BLOCKED: mkdir('%s') is forbidden.\n", path);
                    regs.orig_rax = -1;
                    ptrace(PTRACE_SETREGS, child, NULL, &regs);
                } else {
                    // Optional: Print allow for debugging
                    // printf("[SENTINEL] ✅ ALLOWED: mkdir('%s')\n", path);
                }
            }
            ptrace(PTRACE_SYSCALL, child, NULL, NULL);
        }
        close(fd_req); close(fd_resp);
    }
    return 0;
}