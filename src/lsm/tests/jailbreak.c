// src/lsm/tests/jailbreak.c
// The Ultimate Stress Test for Sentinel M8.2
// Tries to execute 'ping' using multiple evasion techniques.

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define TARGET "/usr/bin/ping"

void try_exec(const char *method) {
  printf("[Jailbreak] Method: %s... ", method);
  // Suppress output of ping to keep log clean (it goes to stderr if blocked)
  // Actually, we want to see the error from perror immediately.
  execl(TARGET, "ping", "-c", "1", "8.8.8.8", NULL);

  // If we are here, exec FAILED (Good!)
  perror("❌ BLOCKED");
  exit(0); // Exit success (blocked)
}

// 1. Direct Child
void test_direct() {
  pid_t pid = fork();
  if (pid == 0) {
    try_exec("Direct Fork");
  }
  int status;
  waitpid(pid, &status, 0);
}

// 2. Grandchild (Double Fork)
void test_grandchild() {
  pid_t pid = fork();
  if (pid == 0) {
    if (fork() == 0) {
      try_exec("Grandchild (Double Fork)");
    }
    exit(0);
  }
  waitpid(pid, NULL, 0);
  sleep(1); // Wait for grandchild
}

// 3. Thread (Clone)
void *thread_func(void *arg) {
  try_exec("Thread (Clone)");
  return NULL;
}

void test_thread() {
  pthread_t t;
  pthread_create(&t, NULL, thread_func, NULL);
  pthread_join(t, NULL);
}

// 4. Shell Injection
void test_shell() {
  pid_t pid = fork();
  if (pid == 0) {
    printf("[Jailbreak] Method: Shell Injection... ");
    // Try to run via sh -c
    execl("/bin/sh", "sh", "-c", TARGET " -c 1 8.8.8.8", NULL);
    perror("❌ BLOCKED (Shell Exec Failed)");
    exit(0);
  }
  int status;
  waitpid(pid, &status, 0);

  // If shell ran ping, ping would print output. If blocked, shell might print
  // "Operation not permitted"
}

int main(int argc, char **argv) {
  printf("==============================================\n");
  printf("⚔️  SENTINEL JAILBREAK SUITE v1.0 ⚔️ \n");
  printf("   PID: %d\n", getpid());
  printf("   WAITING TO BE ARMED...\n");
  printf("==============================================\n");

  // Simulating "Compromise" - wait for user to arm this PID
  if (argc > 1) {
    printf("👉  Running in AUTO-ATTACK MODE (No wait).\n");
    printf("👉  PID: %d (ARM THIS NOW!)\n", getpid());
    sleep(2); // Wait for external script to arm us
  } else {
    printf("👉  Run: sudo ./sentinel_loader mark %d\n", getpid());
    printf("👉  Then press ENTER to launch attacks.\n");
    getchar();
  }

  printf("\n🚀 LAUNCHING EVASION ATTACKS...\n");

  printf("\n--- Phase 1: Direct Attack ---\n");
  test_direct();

  printf("\n--- Phase 2: Evasion (Deep Fork) ---\n");
  test_grandchild();

  printf("\n--- Phase 3: Threading (Clone) ---\n");
  test_thread();

  printf("\n--- Phase 4: Shell Masquerade ---\n");
  test_shell();

  printf("\n==============================================\n");
  printf("✅ TEST COMPLETE.\n");
  return 0;
}
