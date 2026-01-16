#ifndef SENTINEL_LOGGER_H
#define SENTINEL_LOGGER_H

#include <stdio.h>

// Function Prototype
void log_tree_event(int pid, int ppid, int depth, const char* event, const char* extra);

#endif
