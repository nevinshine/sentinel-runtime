#include "logger.h"
#include <string.h>

// ANSI Colors
#define COLOR_RESET   "\033[0m"
#define COLOR_CYAN    "\033[1;36m"
#define COLOR_YELLOW  "\033[1;33m"
#define COLOR_MAGENTA "\033[1;35m"

void log_tree_event(int pid, int ppid, int depth, const char* event, const char* extra) {
    char indent[64] = "";
    const char* color_tag = COLOR_YELLOW;

    // Root
    if (depth == 0) {
        printf(COLOR_CYAN "[SENTINEL]" COLOR_RESET " Attached to Root (PID: %d)\n", pid);
        return;
    }
    
    // Build Indent
    for(int i=0; i<depth-1; i++) strcat(indent, "  │ ");
    strcat(indent, "  └─>");

    // Highlight Grandchild
    if (depth >= 2) color_tag = COLOR_MAGENTA; 

    if (extra) {
        printf("%s %s[%s]" COLOR_RESET " PID: %d (PPID: %d) | %s: %s\n", 
               indent, color_tag, depth >= 2 ? "RECURSIVE" : "TRACKING", 
               pid, ppid, event, extra);
    } else {
        printf("%s %s[%s]" COLOR_RESET " PID: %d (PPID: %d) | %s\n", 
               indent, color_tag, depth >= 2 ? "RECURSIVE" : "TRACKING", 
               pid, ppid, event);
    }
    fflush(stdout);
}
