// Minimal PID hash map for Sentinel Runtime
// src/engine/pidmap.h
#ifndef PIDMAP_H
#define PIDMAP_H
#include <stdlib.h>
#include <stdint.h>

#define PIDMAP_BUCKETS 4096

typedef struct pidmap_entry {
    pid_t pid;
    int depth;
    int syscall_state;
    long syscall_retval;
    struct pidmap_entry *next;
} pidmap_entry_t;

typedef struct pidmap {
    pidmap_entry_t *buckets[PIDMAP_BUCKETS];
} pidmap_t;

static inline uint32_t pidmap_hash(pid_t pid) {
    return ((uint32_t)pid) % PIDMAP_BUCKETS;
}

static inline void pidmap_init(pidmap_t *map) {
    for (int i = 0; i < PIDMAP_BUCKETS; ++i) map->buckets[i] = NULL;
}

static inline pidmap_entry_t *pidmap_get(pidmap_t *map, pid_t pid, int create) {
    uint32_t h = pidmap_hash(pid);
    pidmap_entry_t *e = map->buckets[h];
    while (e) {
        if (e->pid == pid) return e;
        e = e->next;
    }
    if (create) {
        e = (pidmap_entry_t*)calloc(1, sizeof(pidmap_entry_t));
        e->pid = pid;
        e->next = map->buckets[h];
        map->buckets[h] = e;
        return e;
    }
    return NULL;
}

static inline void pidmap_remove(pidmap_t *map, pid_t pid) {
    uint32_t h = pidmap_hash(pid);
    pidmap_entry_t **pp = &map->buckets[h];
    while (*pp) {
        if ((*pp)->pid == pid) {
            pidmap_entry_t *to_free = *pp;
            *pp = (*pp)->next;
            free(to_free);
            return;
        }
        pp = &(*pp)->next;
    }
}

#endif // PIDMAP_H
