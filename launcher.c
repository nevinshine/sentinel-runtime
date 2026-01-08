#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

int main() {
    // 1. Trigger WRITE Interception
    // Sentinel should see this string in its logs
    printf("[IRON SHELL] 🛡️  System Initialized. PID: %d\n", getpid());
    
    // 2. Trigger OPEN Interception
    // Sentinel should detect us touching this file
    printf("[IRON SHELL] Attempting to read /etc/passwd...\n");
    
    FILE *f = fopen("/etc/passwd", "r");
    if (f) {
        printf("[IRON SHELL] Access granted.\n");
        fclose(f);
    } else {
        printf("[IRON SHELL] Access denied.\n");
    }

    return 0;
}
