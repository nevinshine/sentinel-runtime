/*
 * sentinel-runtime: src/engine/main.c
 * RELEASE: Milestone 3.5 (Visuals + Stability + JSON)
 */

#include <sys/ptrace.h>
#include <sys/select.h>
#include <sys/time.h>
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
#include "pidmap.h"
#include "fdmap.h"

// --- VISUALS ---
#define COLOR_CYAN    "\033[1;36m"
#define COLOR_RED     "\033[1;31m"
#define COLOR_GREEN   "\033[1;32m"
#define COLOR_RESET   "\033[0m"

void print_banner() {
    printf("\033[2J\033[1;1H"); // Clear Screen
    printf(COLOR_CYAN);
    printf("   _____            __  _            __\n");
    printf("  / ___/___  ____  / /_(_)___  ___  / /\n");
    printf("  \\__ \\/ _ \\/ __ \\/ __/ / __ \\/ _ \\/ / \n");
    printf(" ___/ /  __/ / / / /_/ / / / /  __/ /  \n");
    printf("/____/\\___/_/ /_/\\__/_/_/ /_/\\___/_/   \n");
    printf(COLOR_RESET);
    printf("   :: Runtime Integrity Engine v3.5 ::\n");
    printf("   [+] Integrity Shield: ACTIVE\n");
    printf("   [+] JSON Protocol:    ACTIVE\n\n");
}

// --- CONFIGURATION ---
const char *get_pipe_req() {
    const char *env = getenv("SENTINEL_PIPE_REQ");
    return env ? env : "/tmp/sentinel_req";
}
const char *get_pipe_resp() {
    const char *env = getenv("SENTINEL_PIPE_RESP");
    return env ? env : "/tmp/sentinel_resp";
}

static pidmap_t pidmap;
static fdmap_t fdmap;

// --- HELPERS ---
void sanitize_json_string(char *str) {
    if (!str) return;
    for (int i = 0; str[i]; i++) {
        if (str[i] == '"' || str[i] == '\\' || str[i] < 32) str[i] = '_';
    }
}

const syscall_sig_t *get_syscall_sig(long sys_num) {
    for (int i = 0; WATCHLIST[i].sys_num != -1; i++) {
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
    fd_set set;
    struct timeval timeout;
    FD_ZERO(&set);
    FD_SET(fd_read, &set);
    timeout.tv_sec = 0;
    timeout.tv_usec = 100000; // 100ms timeout

    int rv = select(fd_read + 1, &set, NULL, NULL, &timeout);
    if (rv <= 0) return 1; // Timeout or Error -> Fail Open
    
    int n = read(fd_read, buf, 1);
    if (n > 0 && buf[0] == '0') return 0; // BLOCK
    return 1; // ALLOW
}

int main(int argc, char *argv[]) {
    fdmap_init(&fdmap);

    // FIXED: Allow ./sentinel <cmd>
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <program> [args...]\n", argv[0]);
        return 1;
    }

    print_banner();

    // --- LAUNCH TARGET ---
    pid_t original_child = fork();
    if (original_child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        raise(SIGSTOP);
        execvp(argv[1], &argv[1]);
        perror("execvp");
        exit(1);
    } 

    // --- PARENT (SENTINEL) ---
    int status;
    struct user_regs_struct regs;

    int fd_req = open(get_pipe_req(), O_WRONLY);
    if (fd_req < 0) { fprintf(stderr, COLOR_RED "[!] IPC Error: Run 'brain.py' first.\n" COLOR_RESET); return 1; }
    int fd_resp = open(get_pipe_resp(), O_RDONLY);

    waitpid(original_child, &status, 0);
    
    pidmap_entry_t *e = pidmap_get(&pidmap, original_child, 1);
    if (e) {
        e->depth = 0;
        printf(COLOR_GREEN "[+] Attached to Target (PID: %d)\n" COLOR_RESET, original_child);
    }

    ptrace(PTRACE_SETOPTIONS, original_child, 0,
            PTRACE_O_TRACEFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC |
            PTRACE_O_EXITKILL | PTRACE_O_TRACEVFORK | PTRACE_O_TRACESYSGOOD);

    ptrace(PTRACE_SYSCALL, original_child, NULL, NULL);

    while (1) {
        pid_t current_pid = waitpid(-1, &status, __WALL);
        if (current_pid == -1) break;

        if (WIFEXITED(status) || WIFSIGNALED(status)) {
            if (current_pid == original_child) break;
            pidmap_remove(&pidmap, current_pid);
            continue;
        }

        e = pidmap_get(&pidmap, current_pid, 1);
        if (!e) { ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL); continue; }

        int event = status >> 16;
        if (event == PTRACE_EVENT_FORK || event == PTRACE_EVENT_CLONE || event == PTRACE_EVENT_VFORK) {
            unsigned long new_pid_l;
            ptrace(PTRACE_GETEVENTMSG, current_pid, 0, &new_pid_l);
            pid_t new_pid = (pid_t)new_pid_l;
            pidmap_entry_t *child = pidmap_get(&pidmap, new_pid, 1);
            if (child) {
                child->depth = e->depth + 1;
                child->syscall_state = 0;
            }
            ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
            continue;
        }

        if (WIFSTOPPED(status) && (WSTOPSIG(status) == (SIGTRAP | 0x80))) {
            ptrace(PTRACE_GETREGS, current_pid, NULL, &regs);
            const syscall_sig_t *sig = get_syscall_sig(regs.orig_rax);

            int is_entry = (e->syscall_state == 0);
            e->syscall_state = !e->syscall_state;

            if (sig) {
                char arg_val[256] = {0};
                long fd_arg = -1;

                if (sig->type == ARG_STRING) {
                    unsigned long addr = (sig->arg_reg_idx == 0) ? regs.rdi : regs.rsi;
                    if (addr != 0) read_string(current_pid, addr, arg_val, 256);
                } else if (sig->type == ARG_INT) {
                    fd_arg = (long)regs.rdi;
                }

                if (!is_entry) {
                    e->syscall_retval = (long)regs.rax;
                    if (e->syscall_retval >= 0) {
                        if (strcmp(sig->name, "open") == 0 || strcmp(sig->name, "openat") == 0)
                            fdmap_set(&fdmap, e->syscall_retval, arg_val, current_pid);
                        else if (strcmp(sig->name, "dup") == 0 || strcmp(sig->name, "dup2") == 0)
                            fdmap_dup(&fdmap, fd_arg, e->syscall_retval, current_pid);
                    }
                    if (strcmp(sig->name, "close") == 0) fdmap_remove(&fdmap, fd_arg, current_pid);
                }

                if (is_entry) {
                    char msg[512];
                    char safe_path[256] = {0};

             if (sig->type == ARG_STRING) {
                        // FIX: Use snprintf to ensure null-termination
                        snprintf(safe_path, sizeof(safe_path), "%s", arg_val);
                    } else if (fd_arg >= 0) {
                        const char *p = fdmap_get(&fdmap, fd_arg, current_pid);
                        if (p) snprintf(safe_path, sizeof(safe_path), "%s", p);
                    }

                    sanitize_json_string(safe_path);

                    snprintf(msg, sizeof(msg),
                        "{\"verb\": \"%s\", \"path\": \"%s\", \"pid\": %d, \"fd\": %ld, \"ret\": %ld}\n",
                        sig->name, safe_path, current_pid, fd_arg, e->syscall_retval);

                    if (write(fd_req, msg, strlen(msg)) != -1) {
                        if (!get_verdict(fd_resp)) {
                            printf("       " COLOR_RED "[BLOCKED]" COLOR_RESET " %s | %s\n", sig->name, safe_path);
                            regs.orig_rax = -1;
                            ptrace(PTRACE_SETREGS, current_pid, NULL, &regs);
                        }
                    }
                }
            }
            ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
        } else {
            ptrace(PTRACE_SYSCALL, current_pid, NULL, NULL);
        }
    }
    close(fd_req);
    close(fd_resp);
    return 0;
}