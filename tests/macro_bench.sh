#!/bin/bash
# tests/macro_bench.sh
# Measures the "User Feel" impact of Sentinel M4

echo "------------------------------------------------"
echo "[*] SETTING UP TEST FILES (Generating 10,000 files)..."
mkdir -p /tmp/sentinel_stress
for i in {1..10000}; do echo "data" > /tmp/sentinel_stress/file_$i.txt; done

echo -e "\n[*] BENCHMARK 1: NATIVE SPEED (No Sentinel)"
# We time a heavy 'find' and 'grep' operation
time (find /tmp/sentinel_stress -type f -exec grep "data" {} + > /dev/null)

echo -e "\n[*] BENCHMARK 2: SENTINEL M4 SPEED"
# We run the SAME heavy operation under Sentinel
time (sudo ./bin/sentinel sh -c 'find /tmp/sentinel_stress -type f -exec grep "data" {} + > /dev/null')

echo -e "\n[*] CLEANING UP..."
rm -rf /tmp/sentinel_stress
echo "------------------------------------------------"
