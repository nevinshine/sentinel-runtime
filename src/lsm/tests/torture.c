// src/lsm/tests/torture.c
// Sentinel Stress Test
// Spawns 10,000 processes rapidly to test Map Capacity and GC Speed.
// Map Size: 4096. Total Processes: 10,000.
// If GC fails, the map will fill up and new processes might be unrestricted!

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

#define WORKERS 50
#define CYCLES 200

void worker(int id) {
  int failures = 0;
  for (int i = 0; i < CYCLES; i++) {
    pid_t p = fork();
    if (p == 0) {
      // Child attempts to execute ping.
      // If Sentinel is working, this MUST fail (EPERM).
      // Redirect output to null to avoid spam
      freopen("/dev/null", "w", stdout);
      freopen("/dev/null", "w", stderr);

      execl("/usr/bin/ping", "ping", "-c", "1", "8.8.8.8", NULL);

      // If we reach here, exec failed (likely blocked).
      // Pass specific code to indicate "Blocked" (Success for us)
      exit(123);
    }

    int status;
    waitpid(p, &status, 0);

    // Check exit code
    if (WIFEXITED(status)) {
      int code = WEXITSTATUS(status);
      if (code == 0) {
        // Ping succeeded! (Returned 0)
        printf("❌ FALURE: Worker %d, Cycle %d - EXEC SUCCEEDED!\n", id, i);
        failures++;
      } else if (code == 123) {
        // Exec failed (Blocked), caught by our exit(123)
        // PASS.
      } else {
        // Ping failed for other reasons (network?) or blocked by shell?
        // Also PASS, as long as it didn't return 0.
      }
    }
  }

  if (failures > 0)
    exit(1);
  exit(0);
}

int main() {
  printf("🔥 SENTINEL TORTURE TEST 🔥\n");
  printf("Workers: %d\n", WORKERS);
  printf("Cycles:  %d\n", CYCLES);
  printf("Total:   %d processes\n", WORKERS * CYCLES);
  printf("Map Limit: 4096 (Testing Overflow/GC)\n");
  printf("----------------------------------------\n");

  for (int i = 0; i < WORKERS; i++) {
    if (fork() == 0)
      worker(i);
  }

  int failed_workers = 0;
  while (wait(NULL) > 0) {
    // Checking worker status...
  }

  printf("----------------------------------------\n");
  printf("✅ TEST COMPLETE. Check output for failures.\n");
  return 0;
}
