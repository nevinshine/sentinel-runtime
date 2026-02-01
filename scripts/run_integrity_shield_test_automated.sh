#!/bin/bash
# run_integrity_shield_test_automated.sh
# This script assumes you have a terminal running: python3 src/analysis/brain.py
# It will run the integrity shield test suite without starting/stopping the brain process.

set -e

PYTHON_BRAIN_LOG=sentinel_brain_integrity_python.log

echo "[TEST] 1. Benign: List directory (should be ALLOW)"
./bin/sentinel open /bin/ls
sleep 1

echo "[TEST] 2. Sensitive file: Write to protected.txt (should be BLOCKED)"
echo "with open('protected.txt', 'w') as f: f.write('hacked')" > write_protected.py
./bin/sentinel write python3 write_protected.py || true
sleep 1

echo "[TEST] 3. Sensitive file: Rename protected.txt (should be BLOCKED)"
echo "import os; os.rename('protected.txt', 'protected2.txt')" > rename_protected.py
./bin/sentinel rename python3 rename_protected.py || true
sleep 1

echo "[TEST] 4. Honeypot: Read honeypot file (should be BLOCKED)"
touch honeypot_secret.txt
./bin/sentinel open /bin/cat honeypot_secret.txt || true
sleep 1

echo "[TEST] 5. Cleanup"
rm -f protected.txt protected2.txt write_protected.py rename_protected.py honeypot_secret.txt

echo "[INFO] Automated Integrity Shield test suite complete. Check your brain.py terminal for block events."
