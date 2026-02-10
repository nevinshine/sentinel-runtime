// tests/sentinel_top.c
// High-Performance C Dashboard for Sentinel
// Uses VT100 escape codes for TUI (No ncurses dependency)

#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysinfo.h>
#include <time.h>
#include <unistd.h>

#define TRACE_PIPE "/sys/kernel/debug/tracing/trace_pipe"
#define HISTORY_LEN 40
#define LOG_LEN 12

// VT100 Macros
#define CLEAR_SCREEN "\033[2J"
#define MOVE_CURSOR(x, y) "\033[%d;%dH", x, y
#define HIDE_CURSOR "\033[?25l"
#define SHOW_CURSOR "\033[?25h"
#define COLOR_RESET "\033[0m"
#define COLOR_RED "\033[31m"
#define COLOR_GREEN "\033[32m"
#define COLOR_YELLOW "\033[33m"
#define COLOR_CYAN "\033[36m"
#define COLOR_WHITE "\033[37m"
#define BG_BLACK "\033[40m"
#define BOLD "\033[1m"

// Global Stats
volatile long total_blocks = 0;
volatile long total_inherits = 0;
volatile long map_usage = 0;
volatile long blocks_per_sec = 0;
volatile long inherits_per_sec = 0;

// History for Graph
long block_history[HISTORY_LEN]; // Circular buffer? No, shift.

// Logs
typedef struct {
  char time[16];
  char pid[16];
  char event[32];
  char details[32];
} log_entry_t;

log_entry_t logs[LOG_LEN];
int log_head = 0; // Ring buffer

volatile int running = 1;

void handle_sig(int sig) { running = 0; }

// Thread: Read Trace Pipe
volatile int connected = 0;

// Thread: Read Trace Pipe
void *reader_thread(void *arg) {
  while (running) {
    FILE *fp = fopen(TRACE_PIPE, "r");
    if (!fp) {
      connected = 0;
      sleep(1);
      continue;
    }

    connected = 1;
    char line[512];
    long b_count = 0;
    long i_count = 0;
    time_t last_check = time(NULL);

    while (running) {
      if (!fgets(line, sizeof(line), fp)) {
        if (ferror(fp)) {
          // Error handling if needed
        }
        break; // EOF or error, close and retry
      }

      // Simple string matching is fast in C
      if (strstr(line, "Sentinel: BLOCKED EXEC")) {
        __sync_fetch_and_add(&total_blocks, 1);
        b_count++;

        // Extract Log Data
        // Format: ... bpf_trace_printk: Sentinel: BLOCKED EXEC TGID 12345 ...
        char *tgid_ptr = strstr(line, "TGID");
        char pid_str[16] = "???";
        if (tgid_ptr)
          sscanf(tgid_ptr, "TGID %15s", pid_str);

        // Add to Log Buffer (Lockless? No, naive ring buffer ok for TUI)
        time_t now = time(NULL);
        struct tm *t = localtime(&now);
        char time_str[16];
        strftime(time_str, sizeof(time_str), "%H:%M:%S", t);

        int idx = log_head % LOG_LEN;
        strcpy(logs[idx].time, time_str);
        strcpy(logs[idx].pid, pid_str);
        strcpy(logs[idx].event, "EXEC_BLOCK");
        strcpy(logs[idx].details, "PING BLOCKED");
        log_head++;
      } else if (strstr(line, "Sentinel: INHERIT")) {
        __sync_fetch_and_add(&total_inherits, 1);
        i_count++;
      }

      // Rate Calculation
      time_t now = time(NULL);
      if (now - last_check >= 1) {
        blocks_per_sec = b_count;
        inherits_per_sec = i_count;

        // Shift History
        memmove(&block_history[0], &block_history[1],
                sizeof(long) * (HISTORY_LEN - 1));
        block_history[HISTORY_LEN - 1] = b_count; // Newest at end

        b_count = 0;
        i_count = 0;
        last_check = now;
      }
    }
    fclose(fp);
    connected = 0;
    sleep(1);
  }
  return NULL;
}

// Thread: Update Map Stats
void *map_thread(void *arg) {
  while (running) {
    FILE *fp = popen("bpftool map show | grep sentinel_policy | awk '{print "
                     "$1}' | tr -d ':'",
                     "r");
    if (fp) {
      char map_id[16];
      if (fgets(map_id, sizeof(map_id), fp)) {
        map_id[strcspn(map_id, "\n")] = 0;
        pclose(fp);

        // Get count
        char cmd[128];
        snprintf(cmd, sizeof(cmd), "bpftool map dump id %s | grep key | wc -l",
                 map_id);
        fp = popen(cmd, "r");
        if (fp) {
          char count_str[16];
          if (fgets(count_str, sizeof(count_str), fp)) {
            map_usage = atol(count_str);
          }
          pclose(fp);
        }
      } else {
        pclose(fp);
      }
    }
    sleep(1);
  }
  return NULL;
}

void render() {
  char buf[4096];
  int offset = 0;

  // Move Cursor Home (1,1) & Hide
  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     HIDE_CURSOR MOVE_CURSOR(1, 1));

  // Header
  struct sysinfo si;
  sysinfo(&si);
  offset +=
      snprintf(buf + offset, sizeof(buf) - offset,
               BG_BLACK COLOR_WHITE BOLD " SENTINEL KERNEL RUNTIME "
                                         "%s%s " COLOR_RESET
                                         " Uptime: %lds | Load: %.2f \033[K\n",
               connected ? COLOR_GREEN "● ACTIVE" : COLOR_RED "● DISCONNECTED",
               connected ? "" : "", // Placeholder
               si.uptime, si.loads[0] / 65536.0);
  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     "─────────────────────────────────────────────────────────"
                     "─────────────────────\033[K\n");

  // KPIs
  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     COLOR_RED BOLD
                     " VIOLATIONS: %-10ld" COLOR_RESET COLOR_CYAN BOLD
                     " INHERITANCE: %-10ld" COLOR_RESET COLOR_YELLOW BOLD
                     " MAP PRESSURE: %-5ld" COLOR_RESET "\033[K\n",
                     total_blocks, total_inherits, map_usage);
  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     "─────────────────────────────────────────────────────────"
                     "─────────────────────\033[K\n");

  // Graph Check
  long peak = 0;
  for (int i = 0; i < HISTORY_LEN; i++)
    if (block_history[i] > peak)
      peak = block_history[i];

  offset += snprintf(
      buf + offset, sizeof(buf) - offset,
      BOLD " BLOCK RATE (Peak: %ld/s | Cur: %ld/s)\033[K\n" COLOR_RESET, peak,
      blocks_per_sec);

  // Draw Graph (Last 10 entries)
  int start = HISTORY_LEN - 1;
  for (int i = 0; i < 10; i++) {
    int idx = start - i;
    if (idx < 0)
      break;
    long val = block_history[idx];

    // Bar Logic
    if (peak == 0)
      peak = 1;
    int width = 40;
    int filled = (val * width) / peak;

    offset +=
        snprintf(buf + offset, sizeof(buf) - offset, " %ds | " COLOR_RED, i);
    for (int j = 0; j < filled; j++)
      offset += snprintf(buf + offset, sizeof(buf) - offset, "█");
    offset +=
        snprintf(buf + offset, sizeof(buf) - offset, COLOR_WHITE BOLD); // Dim
    for (int j = filled; j < width; j++)
      offset += snprintf(buf + offset, sizeof(buf) - offset, "░");
    offset += snprintf(buf + offset, sizeof(buf) - offset,
                       COLOR_RESET " %ld\033[K\n", val);
  }

  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     "─────────────────────────────────────────────────────────"
                     "─────────────────────\033[K\n");
  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     BOLD " LIVE LOGS\033[K\n" COLOR_RESET);
  offset += snprintf(buf + offset, sizeof(buf) - offset,
                     " TIME      PID       EVENT          DETAILS\033[K\n");

  // Logs (Newest first)
  for (int i = 0; i < LOG_LEN; i++) {
    int idx = (log_head - 1 - i + LOG_LEN * 100) % LOG_LEN;
    if (logs[idx].event[0] == 0) {
      offset += snprintf(buf + offset, sizeof(buf) - offset,
                         "\033[K\n"); // Empty line
      continue;
    }
    offset += snprintf(
        buf + offset, sizeof(buf) - offset,
        " %-8s  %-8s  " COLOR_RED "%-12s" COLOR_RESET "   %s\033[K\n",
        logs[idx].time, logs[idx].pid, logs[idx].event, logs[idx].details);
  }

  // Clear rest of screen
  offset += snprintf(buf + offset, sizeof(buf) - offset, "\033[J");

  // Print buffer
  printf("%s", buf);
  fflush(stdout);
}

int main() {
  signal(SIGINT, handle_sig);
  signal(SIGTERM, handle_sig);

  printf(CLEAR_SCREEN);
  fflush(stdout);

  pthread_t r_th, m_th;
  pthread_create(&r_th, NULL, reader_thread, NULL);
  pthread_create(&m_th, NULL, map_thread, NULL);

  // Launch Stress Engine (Robustly)
  system("pkill -f stress_engine"); // Cleanup old
  // We expect user to launch attack manually or via run_attack_live?
  // User requested "attack".
  // Let's AUTO-LAUNCH in background if not running?
  // No, let user control it. It's safer.
  // BUT we need to arm it.
  // Wait, the "Torture" script arms itself.
  // We just monitor.

  while (running) {
    render();
    usleep(250000); // 4 FPS
  }

  printf(SHOW_CURSOR);
  printf("\nExiting...\n");
  return 0;
}
