#!/bin/bash
# sentinel_integrity_shield_test.sh
# Test script for aggressive Integrity Shield policy in Sentinel Runtime

set -e

PYTHON_BRAIN_LOG=sentinel_brain_integrity.log
pkill -f brain.py || true
nohup python3 src/analysis/brain.py > "$PYTHON_BRAIN_LOG" 2>&1 &
BRAIN_PID=$!
sleep 2

echo "[TEST] 1. Benign: List directory (should be ALLOW)"
./bin/sentinel open /bin/ls
sleep 1

echo "[TEST] 2. Sensitive file: Write to protected.txt (should be BLOCKED)"
touch protected.txt
./bin/sentinel write /bin/sh -c 'echo hacked > protected.txt' || true
sleep 1

echo "[TEST] 3. Sensitive file: Rename protected.txt (should be BLOCKED)"
mv protected.txt protected2.txt
./bin/sentinel rename /bin/mv protected2.txt protected3.txt || true
sleep 1

echo "[TEST] 4. Honeypot: Read honeypot file (should be BLOCKED)"
touch honeypot_secret.txt
./bin/sentinel open /bin/cat honeypot_secret.txt || true
sleep 1

echo "[TEST] 5. Cleanup"
rm -f protected.txt protected2.txt protected3.txt honeypot_secret.txt
kill $BRAIN_PID
sleep 1

echo "[INFO] Integrity Shield test suite complete. See $PYTHON_BRAIN_LOG for details."
