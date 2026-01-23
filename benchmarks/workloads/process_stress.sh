#!/bin/bash
# Workload: Process Spawn Stress Test
# Spawns many short-lived processes

COUNT=${1:-500}

echo "[*] Process Stress Test: $COUNT spawns"

START=$(date +%s.%N)
for i in $(seq 1 $COUNT); do
    /bin/true
done
END=$(date +%s.%N)

ELAPSED=$(echo "$END - $START" | bc)
RATE=$(echo "scale=2; $COUNT / $ELAPSED" | bc)

echo "    Total time: $ELAPSED seconds"
echo "    Rate: $RATE processes/sec"
echo "[*] Done!"