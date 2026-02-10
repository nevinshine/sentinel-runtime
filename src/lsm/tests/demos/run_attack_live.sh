#!/bin/bash
# tests/run_attack_live.sh
# Launches the Torture Swarm (10k processes) WITHOUT resetting Sentinel.
# Designed to be run while the Dashboard is open.

# Setup Colors
R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${R}Run as root (sudo)!${NC}"
  exit 1
fi

echo -e "${Y}🔥 PREPARING ATTACK SWARM...${NC}"

# 1. Compile Torture Binary
gcc -o tests/torture tests/torture.c
if [ ! -f tests/torture ]; then
    echo -e "${R}Build failed!${NC}"
    exit 1
fi

# 2. Arm THIS shell (So the attack inherits the restriction)
# We use the Sentinel Loader to mark our PID
./sentinel_loader mark $$ > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${G}💀 TARGET LOCKED (PID $$ marked).${NC}"
else
    echo -e "${R}Failed to arm trigger! Is Sentinel running?${NC}"
    exit 1
fi

# 3. Launch the Swarm
echo -e "${Y}🚀 LAUNCHING 10,000 WARHEADS...${NC}"
echo -e "${Y}   (Watch the Dashboard!)${NC}"
sleep 1 # Give user a second to look at the graph

./tests/torture

echo -e "${G}✅ ATTACK WAVES COMPLETE.${NC}"
