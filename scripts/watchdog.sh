#!/bin/bash
# Sentinel Watchdog (M3.4)
# "Self-Healing Persistence"

# Use absolute paths for reliability
BINARY="./bin/sentinel"

# FIX 1: Provide the required arguments for main.c
# Format: <syscall_name_placeholder> <target_program> <target_args>
# We use 'sleep infinity' so Sentinel has a long-running process to monitor.
ARGS="monitor sleep infinity"

# FIX 2: Use /tmp for logs to avoid permission errors during the demo
LOG_FILE="/tmp/sentinel_watchdog.log"

echo "[*] Sentinel Watchdog Active."
echo "[*] Monitoring process integrity..."

while true; do
    # Check if sentinel is running
    if ! pgrep -x "sentinel" > /dev/null; then
        echo "[!] ALERT: Sentinel process missing!"
        echo "[+] RECOVERY: Restarting security stack..."

        # Run Sentinel in background, piping output to /dev/null to keep terminal clean
        sudo $BINARY $ARGS > /dev/null 2>&1 &

        # Log the recovery event
        echo "$(date): Sentinel resurrected by Watchdog" >> "$LOG_FILE"
    fi
    sleep 5
done