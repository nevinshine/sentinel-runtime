#!/bin/bash
# Workload: File Operations Stress Test
# Creates, writes, reads, and deletes many files

COUNT=${1:-1000}
DIR="/tmp/sentinel_workload_$$"

echo "[*] File Stress Test: $COUNT files"
mkdir -p "$DIR"

# Create & Write
echo "[*] Creating files..."
START=$(date +%s.%N)
for i in $(seq 1 $COUNT); do
    echo "test data $i" > "$DIR/file_$i.txt"
done
END=$(date +%s.%N)
echo "    Create: $(echo "$END - $START" | bc) seconds"

# Read
echo "[*] Reading files..."
START=$(date +%s.%N)
for i in $(seq 1 $COUNT); do
    cat "$DIR/file_$i.txt" > /dev/null
done
END=$(date +%s.%N)
echo "    Read: $(echo "$END - $START" | bc) seconds"

# Delete
echo "[*] Deleting files..."
START=$(date +%s.%N)
rm -rf "$DIR"
END=$(date +%s.%N)
echo "    Delete: $(echo "$END - $START" | bc) seconds"

echo "[*] Done!"