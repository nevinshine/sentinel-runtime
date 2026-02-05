/* tests/bench_throughput.c */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <sys/syscall.h>
#include <fcntl.h>

#define ITERATIONS 10000000 // 10 Million Calls

// Timer Helper
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}

int main() {
    printf("[*] STARTING SENTINEL THROUGHPUT BENCHMARK\n");
    printf("    Target: %d Iterations\n", ITERATIONS);

    // --- TEST 1: The "Fast Path" (Allowed Syscalls) ---
    // In M3 (Ptrace), this was SLOW (~54x overhead).
    // In M4 (Seccomp), this should be INSTANT (Native speed).
    printf("\n[1] Testing FAST PATH (getpid tight loop)...\n");
    
    double start = get_time();
    for (int i = 0; i < ITERATIONS; i++) {
        syscall(__NR_getpid); // Harmless syscall
    }
    double end = get_time();
    
    double duration = end - start;
    double ops = ITERATIONS / duration;
    
    printf("    Duration: %.4f seconds\n", duration);
    printf("    Throughput: %.0f OPS (Calls/Sec)\n", ops);
    if (ops > 2000000) {
        printf("    [VERDICT] 🚀 NATIVE SPEED (Seccomp is working!)\n");
    } else {
        printf("    [VERDICT] 🐢 PTRACE SPEED (Too slow!)\n");
    }

    // --- TEST 2: The "Slow Path" (Trapped Syscalls) ---
    // These are the dangerous ones we actually inspect (openat).
    printf("\n[2] Testing SLOW PATH (openat tight loop)...\n");
    // We do fewer iterations because checking takes time
    int small_iter = 10000; 
    
    start = get_time();
    for (int i = 0; i < small_iter; i++) {
        int fd = syscall(__NR_openat, AT_FDCWD, "/dev/null", O_RDONLY, 0);
        if (fd >= 0) close(fd);
    }
    end = get_time();
    
    duration = end - start;
    double latency_us = (duration / small_iter) * 1000000;
    
    printf("    Duration: %.4f seconds\n", duration);
    printf("    Avg Inspection Latency: %.2f microseconds\n", latency_us);
    
    if (latency_us < 50) {
        printf("    [VERDICT] ⚡ BLAZING FAST (Brain is responding quickly)\n");
    } else {
        printf("    [VERDICT] 🐢 SLOW (Python brain might be lagging)\n");
    }

    return 0;
}
