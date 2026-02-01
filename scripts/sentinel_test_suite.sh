#!/bin/bash
# sentinel_test_suite.sh
# Automated test script for Sentinel Runtime detection logic

set -e

# Start the Python brain in the background (assumes it is not already running)
PYTHON_BRAIN_LOG=sentinel_brain_test.log
pkill -f brain.py || true
nohup python3 src/analysis/brain.py > "$PYTHON_BRAIN_LOG" 2>&1 &
BRAIN_PID=$!
sleep 2

echo "[TEST] 1. Benign: List directory (should be ALLOW)"
./bin/sentinel open /bin/ls
sleep 1

echo "[TEST] 2. Sensitive file: /etc/shadow (should be ALLOW or BLOCK if root)"
./bin/sentinel open /bin/cat /etc/shadow || true
sleep 1

echo "[TEST] 3. Sensitive file: protected.txt (should be MONITOR or BLOCK)"
touch protected.txt
./bin/sentinel open /bin/cat protected.txt
sleep 1

echo "[TEST] 4. Evasion: dup_test (should be ALLOW or MONITOR)"
if [ -f ./bin/dup_test ]; then
  ./bin/sentinel open ./bin/dup_test
else
  echo "[SKIP] dup_test binary not found."
fi
sleep 1

echo "[TEST] 5. Evasion: recursive_fork (should be ALLOW or MONITOR)"
if [ -f ./bin/recursive_fork ]; then
  ./bin/sentinel open ./bin/recursive_fork
else
  echo "[SKIP] recursive_fork binary not found."
fi
sleep 1

echo "[TEST] 6. Cleanup"
rm -f protected.txt
kill $BRAIN_PID
sleep 1

echo "[INFO] Test suite complete. See $PYTHON_BRAIN_LOG for details."
