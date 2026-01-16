// attack.c - PATCHED for Persistence
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>

int main() {
    printf("[MALWARE] Starting infection chain (PID: %d)...\n", getpid());
    
    if (fork() == 0) {
        // Child Process
        printf("[MALWARE] Level 1 dropper active (PID: %d). Spawning payload...\n", getpid());
        
        if (fork() == 0) {
            // Grandchild (Target)
            printf("[MALWARE] Level 2 payload detached (PID: %d). Attempting damage...\n", getpid());
            
            sleep(1); // Give Sentinel time to lock on
            
            // THE TRIGGER
            mkdir("RANSOMWARE_ROOT", 0777); 
            printf("[MALWARE] Payload executed!\n"); // Should never print if Sentinel works
            exit(0);
        }
        
        // Child waits for Grandchild before dying (Keeps tree intact)
        wait(NULL); 
        exit(0);
    }
    
    // Parent waits for Child (Keeps Root intact)
    wait(NULL); 
    printf("[MALWARE] Root exiting.\n");
    return 0;
}
