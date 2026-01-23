#!/bin/bash
# Workload: Mixed Operations (realistic simulation)

echo "[*] Mixed Workload Test"
echo "    Simulates typical shell usage"

# File ops
for i in {1..100}; do
    touch "/tmp/mixed_test_$i.txt"
    echo "data" >> "/tmp/mixed_test_$i.txt"
    cat "/tmp/mixed_test_$i.txt" > /dev/null
done

# Process spawns
for i in {1..50}; do
    ls /tmp > /dev/null
    pwd > /dev/null
    echo "test" | grep "test" > /dev/null
done

# Cleanup
rm -f /tmp/mixed_test_*.txt

echo "[*] Done!"