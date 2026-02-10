// src/lsm/sentinel_loader.c
// Sentinel M8.2: Inode-Only Loader
// Simplified Blocking

#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

#define PIN_PATH "/sys/fs/bpf/sentinel_maps"
#define TARGET_BIN "/usr/bin/ping"

static int stop = 0;
void sig_handler(int signo) { stop = 1; }

// Simplified key (no NS, no Dev)
struct inode_key {
  unsigned long long ino;
};

int setup_map_persistence(struct bpf_object *obj, const char *map_name) {
  char pin_file[256];
  snprintf(pin_file, sizeof(pin_file), "%s/%s", PIN_PATH, map_name);

  struct bpf_map *map = bpf_object__find_map_by_name(obj, map_name);
  if (!map)
    return -1;

  int pinned_fd = bpf_obj_get(pin_file);
  if (pinned_fd >= 0) {
    printf("[Sentinel] Reusing pinned map: %s\n", map_name);
    bpf_map__reuse_fd(map, pinned_fd);
    close(pinned_fd);
  } else {
    bpf_map__set_pin_path(map, pin_file);
  }
  return 0;
}

int mark_pid(int pid) {
  char pin_file[256];
  snprintf(pin_file, sizeof(pin_file), "%s/sentinel_policy", PIN_PATH);
  int fd = bpf_obj_get(pin_file);
  if (fd < 0)
    return -1;
  unsigned int key = (unsigned int)pid, value = 1;
  int ret = bpf_map_update_elem(fd, &key, &value, BPF_ANY);
  close(fd);
  if (ret == 0)
    printf("[Sentinel] ✔️ Marked PID %d as RESTRICTED\n", pid);
  else
    fprintf(stderr, "Failed to mark: %s\n", strerror(errno));
  return ret;
}

void show_policy() {
  char pin_file[256];
  snprintf(pin_file, sizeof(pin_file), "%s/sentinel_policy", PIN_PATH);
  int fd = bpf_obj_get(pin_file);
  if (fd < 0)
    return;
  printf("[Sentinel] Current restricted PIDs:\n");
  unsigned int key = 0, next_key, value;
  int count = 0;
  while (bpf_map_get_next_key(fd, &key, &next_key) == 0) {
    if (bpf_map_lookup_elem(fd, &next_key, &value) == 0) {
      printf("  PID %u\n", next_key);
      count++;
    }
    key = next_key;
  }
  if (count == 0)
    printf("  (none)\n");
  close(fd);
}

int main(int argc, char **argv) {
  if (argc >= 2) {
    if (strcmp(argv[1], "mark") == 0 && argc >= 3)
      return mark_pid(atoi(argv[2]));
    if (strcmp(argv[1], "show") == 0) {
      show_policy();
      return 0;
    }
    if (strcmp(argv[1], "arm") == 0)
      return mark_pid(getppid());
  }

  struct bpf_object *obj;
  struct bpf_link *links[3] = {NULL}; // exec, fork, exit
  struct stat st;

  signal(SIGINT, sig_handler);
  signal(SIGTERM, sig_handler);
  mkdir(PIN_PATH, 0700);

  // Force map cleanup since key structure changed!
  // NO, we rely on the reload script to do this.

  printf("[Sentinel M8.2] Loading Inode-Only Engine...\n");

  obj = bpf_object__open_file("sentinel_lsm.bpf.o", NULL);
  if (libbpf_get_error(obj))
    return 1;

  setup_map_persistence(obj, "sentinel_policy");
  setup_map_persistence(obj, "sentinel_inodes");

  if (bpf_object__load(obj)) {
    fprintf(stderr, "Load failed: %s\n", strerror(errno));
    return 1;
  }

  // Attach exec hook
  struct bpf_program *p_exec =
      bpf_object__find_program_by_name(obj, "sentinel_check_exec");
  links[0] = bpf_program__attach_lsm(p_exec);
  if (libbpf_get_error(links[0]))
    return 1;
  printf("[+] Attached LSM: Exec Check\n");

  // Attach fork inheritance
  struct bpf_program *p_fork =
      bpf_object__find_program_by_name(obj, "sentinel_fork_inherit");
  links[1] = bpf_program__attach(p_fork);
  printf("[+] Attached TP: Inheritance\n");

  // Attach exit GC
  struct bpf_program *p_exit =
      bpf_object__find_program_by_name(obj, "sentinel_exit_gc");
  links[2] = bpf_program__attach(p_exit);
  printf("[+] Attached TP: GC\n");

  // Block Targets (Robustly)
  const char *targets[] = {"/bin/ping", "/usr/bin/ping", "/sbin/ping",
                           "/usr/sbin/ping", NULL};

  for (int i = 0; targets[i]; i++) {
    if (stat(targets[i], &st) == 0) {
      struct inode_key key = {.ino = st.st_ino};
      unsigned int val = 1;
      int map_fd = bpf_object__find_map_fd_by_name(obj, "sentinel_inodes");
      bpf_map_update_elem(map_fd, &key, &val, BPF_ANY);
      printf("[+] BLOCKED: %s (inode=%llu)\n", targets[i],
             (unsigned long long)st.st_ino);
    }
  }

  printf("\n[Sentinel] ENGINE ACTIVE. Press Ctrl+C to stop.\n");
  while (!stop)
    sleep(1);

  for (int i = 0; i < 3; i++)
    bpf_link__destroy(links[i]);
  bpf_object__close(obj);
  return 0;
}