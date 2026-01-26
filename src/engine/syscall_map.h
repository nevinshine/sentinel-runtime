/*
 * sentinel-runtime: src/engine/syscall_map.h
 * RESEARCH ARTIFACT: Universal Syscall Signature Map
 * UPDATED: M3.2 - Added Resource Duplication Tracking for Robustness
 */

#ifndef SYSCALL_MAP_H
#define SYSCALL_MAP_H

#include <sys/syscall.h>
#include <stddef.h>

/* * Argument Types for Extraction Strategy
 * Defines how the engine should read memory from the tracee
 */
typedef enum {
    ARG_NONE,       // No argument extraction needed
    ARG_STRING,     // Null-terminated string (e.g., file paths)
    ARG_INT,        // Integer value (e.g., file descriptors, flags)
    ARG_SOCKADDR    // Socket address structure (for network)
} arg_type_t;

/* * Syscall Signature Structure
 * Maps kernel syscall numbers to semantic analysis data
 */
typedef struct {
    long sys_num;       // The syscall number (from sys/syscall.h)
    const char *name;   // Human-readable name for logging
    int arg_reg_idx;    // Register index of critical argument (0=RDI, 1=RSI, etc.)
    arg_type_t type;    // How to interpret the argument
} syscall_sig_t;

/*
 * THE WATCHLIST
 * Critical system calls intercepted by Sentinel Runtime.
 * NOTE: The {-1, NULL} entry serves as the loop terminator.
 */
static const syscall_sig_t WATCHLIST[] = {
    /* --- File System Integrity (Anti-Ransomware) --- */
    { SYS_mkdir,    "mkdir",    0, ARG_STRING },
    { SYS_unlink,   "unlink",   0, ARG_STRING },
    { SYS_rmdir,    "rmdir",    0, ARG_STRING },
    { SYS_unlinkat, "unlinkat", 1, ARG_STRING }, // Path is 2nd arg (index 1)
    { SYS_rename,   "rename",   0, ARG_STRING },

    /* --- Process Execution & Access --- */
    { SYS_execve,   "execve",   0, ARG_STRING },
    { SYS_openat,   "openat",   1, ARG_STRING }, // Path is 2nd arg (index 1)
    { SYS_open,     "open",     0, ARG_STRING },

    /* --- Data Flow (Exfiltration Detection) --- */
    { SYS_read,     "read",     0, ARG_INT },    // Track data entering memory
    { SYS_write,    "write",    0, ARG_INT },    // Track data leaving memory

    /* --- Resource Management (Evasion Prevention) --- */
    /* CRITICAL FIX: Track FD cloning to prevent malware from hiding sockets */
    { SYS_dup,      "dup",      0, ARG_INT },
    { SYS_dup2,     "dup2",     0, ARG_INT },
    { SYS_dup3,     "dup3",     0, ARG_INT },

    /* --- Network Operations (The Exit Nodes) --- */
    { SYS_socket,   "socket",   0, ARG_INT },
    { SYS_connect,  "connect",  0, ARG_INT },
    { SYS_sendto,   "sendto",   0, ARG_INT },
    { SYS_sendmsg,  "sendmsg",  0, ARG_INT },

    /* --- Cleanup & State Reset --- */
    { SYS_close,    "close",    0, ARG_INT },

    /* --- Terminator --- */
    { -1, NULL, 0, ARG_NONE }
};

#endif