/*
 * sentinel-runtime: src/engine/main.c
 * RELEASE: Milestone 3.1 (Exfiltration State Machine Support)
 */

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
#include "syscall_map.h"

#define PIPE_REQ "/tmp/sentinel_req"
#define PIPE_RESP "/tmp/sentinel_resp"
#define MAX_PIDS 4194304
#define COLOR_RED     "\033[1;31m"
#define COLOR_YELLOW  "\033[1;33m"
#define COLOR_RESET   "\033[0m"

int pid_depths[MAX_PIDS] = {0};
int syscall_state[MAX_PIDS] = {0};
long syscall_retval[MAX_PIDS] = {0};

const syscall_sig_t *get_syscall_sig(long sys_num) {
    for (int i = 0; WATCHLIST[i]. sys_num != -1; i++) {
        if (WATCHLIST[i].sys_num == sys_num) return &WATCHLIST[i];
    }
    return NULL;
}

void read_string(pid_t pid, unsigned long addr, char *str, int max_len) {
    int len = 0;
    unsigned long word;
    while (len < max_len) {
        errno = 0;
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
    if (n > 0 && buf[0] == '0') return 0;
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <syscall_name> <program> [args... ]\n", argv[0]);
        return 1;
    }
    memset(pid_depths, 0, sizeof(pid_depths));
    memset(syscall_state, 0, sizeof(syscall_state));
    memset(syscall_retval, 0, sizeof(syscall_retval));

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
        if (fd_req < 0) { fprintf(stderr, "Sentinel IPC Error:  Pipe not found.\n"); return 1; }
        int fd_resp = open(PIPE_RESP, O_RDONLY);

        waitpid(original_child, &status, 0);
        pid_depths[original_child] = 0;
        log_tree_event(original_child, getpid(), 0, "INIT", "Sentinel Attached (M3.1)");

        ptrace(PTRACE_SETOPTIONS, original_child, 0,
               PTRACE_O_TRACEFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC |
               PTRACE_O_EXITKILL | PTRACE_O_TRACEVFORK | PTRACE_O_TRACESYSGOOD);

        ptrace(PTRACE_SYSCALL, original_child, NULL, NULL);

        while (1) {
            pid_t current_pid = waitpid(-1, &status, __WALL);
            if (current_pid == -1) break;

            if (WIFEXITED(status) || WIFSIGNALED(status)) {
                if (current_pid == original_child) break;
                continue;
            }

            int event = status >> 16;
            if (event == PTRACE_EVENT_FORK || event == PTRACE_EVENT_CLONE || event == PTRACE_EVENT_VFORK) {
                unsigned long new_pid_l;
                ptrace(PTRACE_GETEVENTMSG, current_pid, 0, &new_pid_l);
                pid_t new_pid = (pid_t)new_pid_l;

                pid_depths[new_pid] = pid_depths[current_pid] + 1;
                syscall_state[new_pid] = 0;

                log_tree_event(new_pid, current_pid, pid_depths[new_pid], "SPAWNED", "New Child Process");

                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
                continue;
            }

            if (WIFSTOPPED(status) && (WSTOPSIG(status) == (SIGTRAP | 0x80))) {
                ptrace(PTRACE_GETREGS, current_pid, NULL, &regs);

                const syscall_sig_t *sig = get_syscall_sig(regs.orig_rax);

                int is_entry = (syscall_state[current_pid] == 0);
                syscall_state[current_pid] = ! syscall_state[current_pid];

                if (sig) {
                    char arg_val[256] = {0};
                    unsigned long arg_addr = 0;
                    long fd_arg = -1;

                    if (sig->arg_reg_idx == 0) arg_addr = regs.rdi;
                    else if (sig->arg_reg_idx == 1) arg_addr = regs.rsi;
                    else if (sig->arg_reg_idx == 2) arg_addr = regs.rdx;

                    if (sig->type == ARG_STRING && arg_addr != 0) {
                        read_string(current_pid, arg_addr, arg_val, 256);
                    }

                    if (sig->type == ARG_INT) {
                        fd_arg = (long)regs.rdi;
                    }

                    if (! is_entry) {
                        syscall_retval[current_pid] = (long)regs.rax;
                    }

                    if (is_entry) {
                        char msg[512];

                        if (sig->type == ARG_STRING) {
                            snprintf(msg, sizeof(msg),
                                "SYSCALL:%s:%s: pid=%d:fd=%ld:ret=%ld\n",
                                sig->name, arg_val, current_pid, fd_arg,
                                syscall_retval[current_pid]);
                        } else {
                            snprintf(msg, sizeof(msg),
                                "SYSCALL:%s:%ld:pid=%d: fd=%ld: ret=%ld\n",
                                sig->name, fd_arg, current_pid, fd_arg,
                                syscall_retval[current_pid]);
                        }

                        if (write(fd_req, msg, strlen(msg)) != -1) {
                            if (! get_verdict(fd_resp)) {
                                printf("       " COLOR_RED "[BLOCKED]" COLOR_RESET
                                       " PID:  %d | Action: %s | Target: %s | FD:  %ld\n",
                                       current_pid, sig->name, arg_val, fd_arg);
                                regs. orig_rax = -1;
                                ptrace(PTRACE_SETREGS, current_pid, NULL, &regs);
                            }
                        }
                    }
                }
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            } else if (WIFSTOPPED(status)) {
                ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            }
        }
        close(fd_req);
        close(fd_resp);
    }
    return 0;
}