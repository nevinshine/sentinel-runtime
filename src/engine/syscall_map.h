/*
 * sentinel-runtime: src/engine/syscall_map.h
 * RESEARCH ARTIFACT: Universal Syscall Signature Map
 */

#ifndef SYSCALL_MAP_H
#define SYSCALL_MAP_H

#include <sys/syscall.h> 
#include <stddef.h>  // [FIX] Required for NULL

// Data Types for Argument Extraction
typedef enum {
    ARG_NONE,
    ARG_STRING,      // "filename", "/bin/sh" (Null-terminated)
    ARG_INT,         // flags, mode (Integers)
    ARG_SOCKADDR     // struct sockaddr (Reserved for Phase 7: Network)
} arg_type_t;

// The Signature of a Syscall
typedef struct {
    long sys_num;       // e.g., 59 for execve
    const char *name;   // "execve" (for logging)
    int arg_reg_idx;    // Which register has the critical data? (0=RDI, 1=RSI, etc.)
    arg_type_t type;    // How should the engine read this memory?
} syscall_sig_t;

// --- THE RESEARCH WATCHLIST (Critical 5) ---
// Maps syscalls to their critical argument registers (x86_64 ABI)
// Register Mapping: RDI=0, RSI=1, RDX=2

static const syscall_sig_t WATCHLIST[] = {
    // 1. File Creation
    { SYS_mkdir,   "mkdir",   0, ARG_STRING }, // RDI = pathname
    
    // 2. File Destruction (The FIX: Added unlinkat)
    { SYS_unlink,  "unlink",  0, ARG_STRING }, // RDI = pathname (Legacy)
    { SYS_rmdir,   "rmdir",   0, ARG_STRING }, // RDI = pathname
    { SYS_unlinkat,"unlink",  1, ARG_STRING }, // RSI = pathname (Modern rm uses this!)
    
    // 3. Execution
    { SYS_execve,  "execve",  0, ARG_STRING }, // RDI = filename
    
    // 4. Movement
    { SYS_rename,  "rename",  0, ARG_STRING }, // RDI = oldname
    
    // 5. File Access
    { SYS_openat,  "openat",  1, ARG_STRING }, // RSI = path
    { SYS_open,    "open",    0, ARG_STRING }, // RDI = path
    
    // Sentinel Marker (End of List)
    { -1, NULL, 0, ARG_NONE }
};

#endif
