/* src/main.c */
#define _GNU_SOURCE
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>      // <--- NEW: For file control

#define PIPE_PATH "/tmp/sentinel_ipc" // <--- NEW: The Pipe Address

// ... (Keep your read_string and fatal functions exactly the same) ...
void fatal(const char *msg) {
    perror(msg);
    exit(1);
}

void read_string(pid_t child, unsigned long addr, char *buffer, int max_len) {
    // ... (Keep this function exactly as it was) ...
    // (I am hiding it here to save space, but DO NOT DELETE IT from your code)
    int bytes_read = 0;
    unsigned long word;
    char *ptr = (char *)&word;

    while (bytes_read < max_len) {
        word = ptrace(PTRACE_PEEKDATA, child, addr + bytes_read, NULL);
        if (errno != 0 && bytes_read == 0) { break; }
        for (int i = 0; i < sizeof(long); i++) {
            if (bytes_read >= max_len) break;
            buffer[bytes_read] = ptr[i];
            if (buffer[bytes_read] == '\0') { return; }
            bytes_read++;
        }
    }
    buffer[max_len - 1] = '\0';
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <program>\n", argv[0]);
        return 1;
    }

    // --- NEW: Open the Pipe ---
    printf("[SENTINEL] Connecting to Brain at %s...\n", PIPE_PATH);
    FILE *pipe_fp = fopen(PIPE_PATH, "w"); // Open for Writing
    if (pipe_fp == NULL) {
        perror("Failed to open pipe (Is the Python bridge running?)");
        return 1;
    }
    // ---------------------------

    pid_t child = fork();
    if (child == 0) {
        ptrace(PTRACE_TRACEME, 0, NULL, NULL);
        raise(SIGSTOP);
        execvp(argv[1], &argv[1]);
        fatal("execvp failed");
    } else {
        int status;
        struct user_regs_struct regs;
        char filename[256];

        waitpid(child, &status, 0);
        ptrace(PTRACE_SETOPTIONS, child, 0, PTRACE_O_EXITKILL);
        
        // --- NEW: Signal Connection Success ---
        printf("[SENTINEL] Connected! Monitoring PID: %d\n", child);
        
        while(1) {
            ptrace(PTRACE_SYSCALL, child, NULL, NULL);
            waitpid(child, &status, 0);
            if (WIFEXITED(status)) break;

            ptrace(PTRACE_GETREGS, child, NULL, &regs);

            if ((long)regs.rax == -38 && regs.orig_rax == 83) { // mkdir entry
                read_string(child, regs.rdi, filename, sizeof(filename));

                // --- NEW: TRANSMIT TO PYTHON ---
                // Format: "SYSCALL:mkdir:filename"
                fprintf(pipe_fp, "SYSCALL:mkdir:%s\n", filename);
                fflush(pipe_fp); // FORCE the data out immediately
                // -------------------------------

                printf("[SENTINEL] Sent to Brain: %s\n", filename);

                // (Keep the blocking logic for now as a fallback)
                if (strstr(filename, "malware") != NULL) {
                    regs.orig_rax = -1;
                    ptrace(PTRACE_SETREGS, child, NULL, &regs);
                }
            } 
        }
        fclose(pipe_fp); // Close the pipe when done
    }
    return 0;
}
