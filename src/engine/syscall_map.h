/*
* sentinel-runtime:  src/engine/syscall_map.h
 * RESEARCH ARTIFACT: Universal Syscall Signature Map
 * UPDATED: M3.1 - Added syscalls for Exfiltration State Machine
 */

#ifndef SYSCALL_MAP_H
#define SYSCALL_MAP_H

#include <sys/syscall.h>
#include <stddef.h>

typedef enum {
    ARG_NONE,
    ARG_STRING,
    ARG_INT,
    ARG_SOCKADDR
} arg_type_t;

typedef struct {
    long sys_num;
    const char *name;
    int arg_reg_idx;
    arg_type_t type;
} syscall_sig_t;

static const syscall_sig_t WATCHLIST[] = {
    { SYS_mkdir,    "mkdir",    0, ARG_STRING },
    { SYS_unlink,   "unlink",   0, ARG_STRING },
    { SYS_rmdir,    "rmdir",    0, ARG_STRING },
    { SYS_unlinkat, "unlinkat", 1, ARG_STRING },
    { SYS_execve,   "execve",   0, ARG_STRING },
    { SYS_rename,   "rename",   0, ARG_STRING },
    { SYS_openat,   "openat",   1, ARG_STRING },
    { SYS_open,     "open",     0, ARG_STRING },
    { SYS_read,     "read",     0, ARG_INT },
    { SYS_write,    "write",    0, ARG_INT },
    { SYS_socket,   "socket",   0, ARG_INT },
    { SYS_connect,  "connect",  0, ARG_INT },
    { SYS_sendto,   "sendto",   0, ARG_INT },
    { SYS_sendmsg,  "sendmsg",  0, ARG_INT },
    { SYS_close,    "close",    0, ARG_INT },
    { -1, NULL, 0, ARG_NONE }
};

#endif