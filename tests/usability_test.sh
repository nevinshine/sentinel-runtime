#!/bin/bash
# tests/usability_test.sh
# Scenario: Normal daily usage. Sentinel should ALLOW all of this.

echo "----------------------------------------"
echo "[USER] Starting Daily Life Simulation..."
echo "----------------------------------------"

# 1. Setup a sensitive file (using the Symlink trick to be sure Sentinel is watching)
echo "SECRET_DATA_FOR_WORK" > protected_work.txt
ln -sf protected_work.txt project_notes.txt

# 2. task: View the file (cat)
echo "[USER] Task 1: Reading file contents..."
cat project_notes.txt
if [ $? -eq 0 ]; then echo -e "\033[0;32m[PASS] Reading allowed.\033[0m"; else echo -e "\033[0;31m[FAIL] Reading blocked!\033[0m"; fi

# 3. Task: Make a backup (cp)
echo "[USER] Task 2: Backing up file..."
cp project_notes.txt backup_notes.txt
if [ $? -eq 0 ]; then echo -e "\033[0;32m[PASS] Backup allowed.\033[0m"; else echo -e "\033[0;31m[FAIL] Backup blocked!\033[0m"; fi

# 4. Task: Search inside file (grep)
echo "[USER] Task 3: Searching content..."
grep "SECRET" project_notes.txt
if [ $? -eq 0 ]; then echo -e "\033[0;32m[PASS] Search allowed.\033[0m"; else echo -e "\033[0;31m[FAIL] Search blocked!\033[0m"; fi

# Cleanup
rm protected_work.txt project_notes.txt backup_notes.txt
echo "----------------------------------------"
echo "[SUCCESS] Daily life is unaffected."