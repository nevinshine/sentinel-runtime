/*
 * sentinel-runtime: src/engine/main.c
 * RELEASE: Milestone 4.0 (Seccomp-BPF + ADDFD Injection)
 * DEFENSE: Blocks io_uring, Traps eBPF, Atomic TOCTOU Mitigation
 */

#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/ioctl.h>
#include <sys/uio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <stddef.h>

// --- VISUALS ---
#define COLOR_RED     "\033[1;31m"
#define COLOR_GREEN   "\033[1;32m"
#define COLOR_YELLOW  "\033[1;33m"
#define COLOR_RESET   "\033[0m"

const char *get_pipe_req() { return getenv("SENTINEL_PIPE_REQ") ? getenv("SENTINEL_PIPE_REQ") : "/tmp/sentinel_req"; }
const char *get_pipe_resp() { return getenv("SENTINEL_PIPE_RESP") ? getenv("SENTINEL_PIPE_RESP") : "/tmp/sentinel_resp"; }

// --- IPC HELPERS ---
int send_fd(int sock, int fd) {
    struct msghdr msg = {0};
    char buf[CMSG_SPACE(sizeof(int))];
    memset(buf, 0, sizeof(buf));
    struct iovec io = { .iov_base = "1", .iov_len = 1 };
    msg.msg_iov = &io; msg.msg_iovlen = 1; msg.msg_control = buf; msg.msg_controllen = sizeof(buf);
    struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
    cmsg->cmsg_level = SOL_SOCKET; cmsg->cmsg_type = SCM_RIGHTS; cmsg->cmsg_len = CMSG_LEN(sizeof(int));
    *((int *)CMSG_DATA(cmsg)) = fd;
    return sendmsg(sock, &msg, 0);
}

int recv_fd(int sock) {
    struct msghdr msg = {0};
    char buf[CMSG_SPACE(sizeof(int))];
    memset(buf, 0, sizeof(buf));
    char nothing;
    struct iovec io = { .iov_base = &nothing, .iov_len = 1 };
    msg.msg_iov = &io; msg.msg_iovlen = 1; msg.msg_control = buf; msg.msg_controllen = sizeof(buf);
    if (recvmsg(sock, &msg, 0) < 0) return -1;
    struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
    return *((int *)CMSG_DATA(cmsg));
}

// --- SECCOMP INSTALLER ---
int install_filter(int sock_fd) {
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, (offsetof(struct seccomp_data, arch))),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, (offsetof(struct seccomp_data, nr))),

        // [VECTOR A] Block Ghost Tunnel (io_uring)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_io_uring_setup, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_io_uring_enter, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),

        // [VECTOR B] Trap Invisible Enemy (eBPF)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_bpf, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF),

        // [VECTOR C] Trap Criticals (execve, openat, mprotect)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_execve, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_openat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_connect, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mprotect, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF),

        // PERFORMANCE: Allow everything else
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog prog = { .len = sizeof(filter)/sizeof(filter[0]), .filter = filter };
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) return -1;
    int listener = syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_NEW_LISTENER, &prog);
    if (listener < 0) return -1;
    send_fd(sock_fd, listener);
    close(listener);
    return 0;
}

// --- HELPER: Atomic Injection (The TOCTOU Fix) ---
int inject_fd(int notify_fd, int victim_pid, int local_fd, struct seccomp_notif *req, struct seccomp_notif_resp *resp) {
    struct seccomp_notif_addfd addfd = {0};
    addfd.id = req->id;
    addfd.srcfd = local_fd;
    addfd.newfd = 0; // Let kernel pick, or 0 to alloc
    addfd.flags = SECCOMP_ADDFD_FLAG_SETFD; // Set the FD in victim

    int remote_fd = ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_ADDFD, &addfd);
    if (remote_fd < 0) return -1;

    // We successfully injected! Now tell syscall to "return" this FD
    resp->val = remote_fd;
    resp->error = 0;
    resp->flags = 0; // Do NOT continue syscall (we handled it)
    return 0;
}

int read_remote_string(pid_t pid, unsigned long addr, char *buf, size_t max_len) {
    struct iovec local = {buf, max_len}, remote = {(void*)addr, max_len};
    return process_vm_readv(pid, &local, 1, &remote, 1, 0);
}

// --- MAIN ---
int main(int argc, char *argv[]) {
    if (argc < 2) { fprintf(stderr, "Usage: %s <cmd>\n", argv[0]); return 1; }
    int sv[2]; socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
    int fd_req = open(get_pipe_req(), O_WRONLY);
    int fd_resp = open(get_pipe_resp(), O_RDONLY);

    pid_t child = fork();
    if (child == 0) {
        close(sv[0]); close(fd_req); close(fd_resp);
        if (install_filter(sv[1]) != 0) exit(1);
        execvp(argv[1], &argv[1]);
        exit(1);
    }
    close(sv[1]);
    int notify_fd = recv_fd(sv[0]);
    close(sv[0]);

    printf(COLOR_GREEN "[+] Sentinel M4 Active. Seccomp FD: %d\n" COLOR_RESET, notify_fd);

    while (1) {
        struct seccomp_notif req = {0};
        struct seccomp_notif_resp resp = {0};
        if (ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_RECV, &req) < 0) {
            if (errno == EINTR) continue;
            break;
        }

        resp.id = req.id;
        char msg[512] = {0};
        char path[256] = {0};
        int verdict = 1; // Default Allow

        if (ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_ID_VALID, &req.id) < 0) continue;

        if (req.data.nr == __NR_openat) {
            read_remote_string(req.pid, req.data.args[1], path, 256);
            snprintf(msg, 512, "{\"verb\":\"openat\",\"path\":\"%s\",\"pid\":%d}\n", path, req.pid);
        } else if (req.data.nr == __NR_execve) {
            read_remote_string(req.pid, req.data.args[0], path, 256);
            snprintf(msg, 512, "{\"verb\":\"execve\",\"path\":\"%s\",\"pid\":%d}\n", path, req.pid);
        } else if (req.data.nr == __NR_bpf) {
            snprintf(msg, 512, "{\"verb\":\"bpf\",\"cmd\":%llu,\"pid\":%d}\n", req.data.args[0], req.pid);
            printf(COLOR_RED "[!] eBPF LOAD DETECTED\n" COLOR_RESET);
        } else if (req.data.nr == __NR_mprotect && (req.data.args[2] & 0x4)) {
            snprintf(msg, 512, "{\"verb\":\"mprotect\",\"flags\":\"PROT_EXEC\",\"pid\":%d}\n", req.pid);
        }

        if (msg[0]) {
            write(fd_req, msg, strlen(msg));
            char buf[2] = {0};
            if (read(fd_resp, buf, 1) > 0 && buf[0] == '0') verdict = 0;
        }

        if (verdict == 1 && req.data.nr == __NR_openat) {
            // *** ATOMIC INJECTION (Anti-Race) ***
            // 1. We open the file safely on host
            int local_fd = openat(AT_FDCWD, path, req.data.args[2], req.data.args[3]);
            if (local_fd >= 0) {
                // 2. Inject it into victim
                if (inject_fd(notify_fd, req.pid, local_fd, &req, &resp) == 0) {
                    close(local_fd);
                    ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_SEND, &resp);
                    continue; // Skip the standard response logic
                }
                close(local_fd);
            }
        }
        
        if (verdict == 1) {
            resp.flags = SECCOMP_USER_NOTIF_FLAG_CONTINUE;
        } else {
            resp.error = -EPERM;
        }
        ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_SEND, &resp);
    }
    return 0;
}
