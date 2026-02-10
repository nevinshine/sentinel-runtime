#!/bin/bash
# src/lsm/tests/run_torture.sh
# Automated Stress Test Runner

# Setup Colors
R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${R}Run as root!${NC}"
  exit 1
fi

echo -e "${Y}🔥 BUILDING TORTURE SUITE...${NC}"
gcc -o torture tests/torture.c
if [ ! -f torture ]; then
    echo -e "${R}Build failed!${NC}"
    exit 1
fi

# Reset Sentinel
echo -e "${Y}🛡️  RESETTING SENTINEL (Starting Clean State)...${NC}"
pkill -9 -f sentinel_loader > /dev/null 2>&1
pkill -f "cat /sys/kernel/debug/tracing/trace_pipe" > /dev/null 2>&1
rm -rf /sys/fs/bpf/sentinel_maps > /dev/null 2>&1

./sentinel_loader > /dev/null 2>&1 &
LOADER_PID=$!
sleep 2

# Arm script
echo -e "${G}💀 ARMING TORTURE SCRIPT (PID $$)...${NC}"
./sentinel_loader mark $$ > /dev/null

echo -e "${Y}🚀 LAUNCHING 10,000 PROCESSES... (This may take a few seconds)${NC}"

# Measure time
start=$(date +%s%N)
./torture
end=$(date +%s%N)
duration=$(( (end - start) / 1000000 ))

echo -e "${G}✅ TORTURE COMPLETE in ${duration} ms.${NC}"

# Check for failures in output?
# Torture prints "FAILURE" if any.

echo -e "${Y} Cleaning up...${NC}"
kill $LOADER_PID > /dev/null 2>&1
