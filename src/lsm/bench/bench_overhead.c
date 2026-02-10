// src/lsm/bench/bench_overhead.c
// Micro-benchmark for Sentinel M8 Overhead (Raw Output)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define FORK_ITER 100000
#define EXEC_ITER 10000

long diff_ns(struct timespec t1, struct timespec t2) {
  long sec = t2.tv_sec - t1.tv_sec;
  long nsec = t2.tv_nsec - t1.tv_nsec;
  return sec * 1000000000L + nsec;
}

void bench_fork() {
  struct timespec start, end;
  clock_gettime(CLOCK_MONOTONIC, &start);
  for (int i = 0; i < FORK_ITER; i++) {
    pid_t pid = fork();
    if (pid == 0)
      exit(0);
    wait(NULL);
  }
  clock_gettime(CLOCK_MONOTONIC, &end);

  long total_ns = diff_ns(start, end);
  double avg_ns = (double)total_ns / FORK_ITER;
  // Output raw number
  printf("%.2f\n", avg_ns);
}

void bench_exec() {
  struct timespec start, end;
  const char *target = "/bin/true";

  clock_gettime(CLOCK_MONOTONIC, &start);
  for (int i = 0; i < EXEC_ITER; i++) {
    pid_t pid = fork();
    if (pid == 0) {
      execl(target, "true", NULL);
      perror("execl failed");
      exit(1);
    }
    wait(NULL);
  }
  clock_gettime(CLOCK_MONOTONIC, &end);

  long total_ns = diff_ns(start, end);
  double avg_ns = (double)total_ns / EXEC_ITER;
  // Output raw number
  printf("%.2f\n", avg_ns);
}

int main(int argc, char **argv) {
  if (argc > 1 && strcmp(argv[1], "fork") == 0) {
    bench_fork();
  } else if (argc > 1 && strcmp(argv[1], "exec") == 0) {
    bench_exec();
  } else {
    bench_fork();
    bench_exec();
  }
  return 0;
}
