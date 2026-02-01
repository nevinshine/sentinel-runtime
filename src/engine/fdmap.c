// fdmap.c
#include "fdmap.h"
#include <string.h>

void fdmap_init(fdmap_t *map) {
    map->count = 0;
}

void fdmap_set(fdmap_t *map, int fd, const char *path, pid_t pid) {
    for (size_t i = 0; i < map->count; ++i) {
        if (map->entries[i].fd == fd && map->entries[i].pid == pid) {
            strncpy(map->entries[i].path, path, sizeof(map->entries[i].path)-1);
            map->entries[i].path[sizeof(map->entries[i].path)-1] = '\0';
            return;
        }
    }
    if (map->count < FDMAP_MAX) {
        map->entries[map->count].fd = fd;
        map->entries[map->count].pid = pid;
        strncpy(map->entries[map->count].path, path, sizeof(map->entries[map->count].path)-1);
        map->entries[map->count].path[sizeof(map->entries[map->count].path)-1] = '\0';
        map->count++;
    }
}

const char *fdmap_get(fdmap_t *map, int fd, pid_t pid) {
    for (size_t i = 0; i < map->count; ++i) {
        if (map->entries[i].fd == fd && map->entries[i].pid == pid) {
            return map->entries[i].path;
        }
    }
    return NULL;
}

void fdmap_remove(fdmap_t *map, int fd, pid_t pid) {
    for (size_t i = 0; i < map->count; ++i) {
        if (map->entries[i].fd == fd && map->entries[i].pid == pid) {
            map->entries[i] = map->entries[map->count-1];
            map->count--;
            return;
        }
    }
}

void fdmap_dup(fdmap_t *map, int oldfd, int newfd, pid_t pid) {
    const char *path = fdmap_get(map, oldfd, pid);
    if (path) {
        fdmap_set(map, newfd, path, pid);
    }
}
