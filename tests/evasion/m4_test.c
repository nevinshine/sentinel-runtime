/* tests/evasion/m4_test.c */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <errno.h>
#include <string.h>
#include <linux/io_uring.h>

int main() {
    printf("[*] STARTING SENTINEL M4 SECURITY CHECK...\n");

    // --- TEST 1: The Ghost Tunnel (io_uring) ---
    printf("[1] Testing io_uring_setup (Ghost Tunnel)...\n");
    // We try to setup a ring with 32 entries.
    long ret = syscall(__NR_io_uring_setup, 32, NULL);
    if (ret < 0 && errno == EPERM) {
        printf("    [SUCCESS] BLOCKED! Kernel returned EPERM.\n");
    } else {
        printf("    [FAIL] io_uring allowed! (Ret: %ld)\n", ret);
    }

    // --- TEST 2: The Invisible Enemy (eBPF) ---
    printf("[2] Testing bpf() syscall (Invisible Enemy)...\n");
    // Try to load a map (safest BPF call)
    // Sentinel should see this and ALERT, but might allow it if brain says so
    // or block if strict.
    ret = syscall(__NR_bpf, 0, NULL, 0); // invalid cmd 0, but triggers syscall
    printf("    [INFO] bpf() called. Check Brain logs for ALERT.\n");

    // --- TEST 3: Fileless Malware (W^X Violation) ---
    printf("[3] Testing mprotect(PROT_EXEC) (Fileless Malware)...\n");
    void *mem = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    if (mem == MAP_FAILED) { perror("mmap"); return 1; }
    
    // Try to make it executable
    ret = mprotect(mem, 4096, PROT_READ|PROT_EXEC);
    if (ret == 0) {
        printf("    [WARNING] mprotect allowed (Brain verification needed).\n");
    } else {
        printf("    [SUCCESS] mprotect blocked!\n");
    }

    // --- TEST 4: The Runc Race (Openat) ---
    printf("[4] Testing openat (Critical Path)...\n");
    FILE *f = fopen("/etc/passwd", "r");
    if (f) {
        printf("    [INFO] openat succeeded (Brain allowed it).\n");
        fclose(f);
    } else {
        printf("    [INFO] openat blocked.\n");
    }

    return 0;
}
