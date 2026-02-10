// src/lsm/sentinel_lsm.c
// Sentinel M8.2: Inode-Only Enforcement
// Removes Device ID check to fix mismatch issues.

#include "headers/vmlinux.h"
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";

#ifndef ENOENT
#define ENOENT 2
#endif

#ifndef EPERM
#define EPERM 1
#endif

// ==============================
// [ 0x01 ] DATA STRUCTURES
// ==============================
// Key: Inode ONLY.
// This avoids dev_t mismatch issues between userspace stat and kernel
// sb->s_dev.
struct inode_key {
  u64 ino;
};

// ==============================
// [ 0x02 ] MAPS
// ==============================
struct {
  __uint(type, BPF_MAP_TYPE_LRU_HASH);
  __uint(max_entries, 16384); // Increased for Torture Test (10k swarm)
  __type(key, u32);
  __type(value, u32);
} sentinel_policy SEC(".maps");

struct {
  __uint(type, BPF_MAP_TYPE_LRU_HASH);
  __uint(max_entries, 4096);
  __type(key, struct inode_key);
  __type(value, u32);
} sentinel_inodes SEC(".maps");

// ==============================
// [ 0x03 ] HELPERS
// ==============================
static __always_inline int is_inode_blocked(struct inode *inode) {
  if (!inode)
    return 0;

  struct inode_key key = {};
  key.ino = BPF_CORE_READ(inode, i_ino);

  u32 *blocked = bpf_map_lookup_elem(&sentinel_inodes, &key);
  if (blocked)
    return 1;
  return 0;
}

// ==============================
// [ 0x04 ] CORE LOGIC
// ==============================

// EXEC CHECK
SEC("lsm/bprm_check_security")
int BPF_PROG(sentinel_check_exec, struct linux_binprm *bprm) {
  u32 tgid = bpf_get_current_pid_tgid() >> 32;
  u32 *policy = bpf_map_lookup_elem(&sentinel_policy, &tgid);

  // Check if policy is active
  if (!policy || *policy != 1)
    return 0;

  struct file *file = BPF_CORE_READ(bprm, file);
  if (!file)
    return 0;

  struct inode *i = BPF_CORE_READ(file, f_inode);
  if (!i)
    return 0;

  if (is_inode_blocked(i)) {
    bpf_printk("Sentinel: BLOCKED EXEC TGID %d Inode %llu\n", tgid,
               BPF_CORE_READ(i, i_ino));
    return -EPERM;
  }
  return 0;
}

// INHERITANCE (Fork)
SEC("tp_btf/sched_process_fork")
int BPF_PROG(sentinel_fork_inherit, struct task_struct *parent,
             struct task_struct *child) {
  u32 parent_tgid = BPF_CORE_READ(parent, tgid);
  u32 *parent_policy = bpf_map_lookup_elem(&sentinel_policy, &parent_tgid);

  if (parent_policy && *parent_policy == 1) {
    u32 child_tgid = BPF_CORE_READ(child, tgid);
    u32 value = 1;
    bpf_map_update_elem(&sentinel_policy, &child_tgid, &value, BPF_ANY);
    bpf_printk("Sentinel: INHERIT %d -> %d\n", parent_tgid, child_tgid);
  }
  return 0;
}

// GC (Exit)
SEC("tp_btf/sched_process_exit")
int BPF_PROG(sentinel_exit_gc, struct task_struct *task) {
  u32 tgid = BPF_CORE_READ(task, tgid);
  bpf_map_delete_elem(&sentinel_policy, &tgid);
  return 0;
}