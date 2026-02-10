// tests/stress_engine.c
// High-Velocity Load Generator for Sentinel TUI

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

// Use absolute paths
#define BLOCKED_BIN "/usr/bin/ping"
#define ALLOWED_BIN "/usr/bin/true"

static volatile int keep_running = 1;

void handle_sig(int sig) { keep_running = 0; }

int main(int argc, char *argv[]) {
  signal(SIGINT, handle_sig);
  signal(SIGTERM, handle_sig);

  printf("Starting High-Velocity Stress Engine (PID: %d)...\n", getpid());

  long count = 0;
  while (keep_running) {
    pid_t pid = fork();
    if (pid == 0) {
      // Child: Suppress output for speed
      freopen("/dev/null", "w", stdout);
      freopen("/dev/null", "w", stderr);

      // Alternate between Blocked and Allowed
      if (count % 2 == 0) {
        execl(BLOCKED_BIN, "ping", "-c", "1", "127.0.0.1", NULL);
      } else {
        execl(ALLOWED_BIN, "true", NULL);
      }
      // If blocking works, ping fails, so we exit(1)
      // If execution works, true succeeds, so we exit(0)
      exit(1);
    } else if (pid > 0) {
      waitpid(pid, NULL, 0); // Reaper
    }

    count++;
    // 500 microseconds = 2000 ops/sec potential
    usleep(500);
  }
  return 0;
}
