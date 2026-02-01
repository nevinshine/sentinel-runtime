// fdmap.h
// Simple fd-to-path mapping for Sentinel Runtime
#ifndef FDMAP_H
#define FDMAP_H

#include <stddef.h>
#include <sys/types.h>

#define FDMAP_MAX 1024

struct fdmap_entry {
    int fd;
    char path[256];
    pid_t pid;
};

typedef struct {
    struct fdmap_entry entries[FDMAP_MAX];
    size_t count;
} fdmap_t;

void fdmap_init(fdmap_t *map);
void fdmap_set(fdmap_t *map, int fd, const char *path, pid_t pid);
const char *fdmap_get(fdmap_t *map, int fd, pid_t pid);
void fdmap_remove(fdmap_t *map, int fd, pid_t pid);
void fdmap_dup(fdmap_t *map, int oldfd, int newfd, pid_t pid);

#endif // FDMAP_H
