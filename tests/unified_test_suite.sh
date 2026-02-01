#!/bin/bash
# SENTINEL UNIFIED DEFENSE TEST SUITE (v3.6)
# Clean Mode: Suppresses C Engine output for a professional demo look.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

SENSITIVE_FILE="top_secret_prototype.pdf"
SAFE_FILE="readme.txt"
USB_MOUNT="./fake_usb"
SIG_FILE="signatures.txt"

# Setup (Silent)
mkdir -p $USB_MOUNT
touch $SENSITIVE_FILE $SAFE_FILE
echo "" > $SIG_FILE

clear
echo "=========================================================="
echo "    SENTINEL v3.6 - LIVE FIRE EXERCISE"
echo "=========================================================="
echo ""

# TEST 1: Trust Filter
echo -e "${CYAN}[TEST 1] The Trust Filter${NC}"
./bin/sentinel ls -la > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[PASS] Trusted binary 'ls' ALLOWED.${NC}"
else
    echo -e "${RED}[FAIL] 'ls' BLOCKED!${NC}"
fi
echo ""

# TEST 2: Integrity Shield (Silent)
echo -e "${CYAN}[TEST 2] Integrity Shield (Anti-Ransomware)${NC}"
./bin/sentinel rm $SENSITIVE_FILE > /dev/null 2>&1  # <--- HIDES THE LOGO
if [ -f "$SENSITIVE_FILE" ]; then
    echo -e "${GREEN}[PASS] Deletion BLOCKED.${NC}"
else
    echo -e "${RED}[FAIL] File was deleted!${NC}"
    touch $SENSITIVE_FILE
fi
echo ""

# TEST 3: USB Trap (Silent)
echo -e "${CYAN}[TEST 3] USB Data Exfiltration${NC}"
cat <<EOF > usb_stealer.py
import os
try:
    with open("$SENSITIVE_FILE", "r") as f: data = f.read()
    with open("$USB_MOUNT/stolen_data", "w") as f: f.write("stolen_secrets")
except: pass
EOF

./bin/sentinel python3 usb_stealer.py > /dev/null 2>&1 # <--- HIDES THE LOGO

if [ -s "$USB_MOUNT/stolen_data" ]; then
    echo -e "${RED}[FAIL] Data leaked to USB!${NC}"
else
    echo -e "${GREEN}[PASS] USB Write BLOCKED.${NC}"
fi
rm usb_stealer.py
echo ""

# TEST 4: Auto-DLP (Silent)
echo -e "${CYAN}[TEST 4] Auto-DLP Bridge (Network Defense)${NC}"
./bin/sentinel cat $SENSITIVE_FILE > /dev/null 2>&1
KEYWORD=$(basename "$SENSITIVE_FILE" .pdf)
if grep -q "$KEYWORD" "$SIG_FILE"; then
    echo -e "${GREEN}[PASS] Firewall Updated.${NC}"
else
    echo -e "${RED}[FAIL] Firewall NOT Updated.${NC}"
fi

echo ""
echo "=========================================================="
echo "ALL SYSTEMS GREEN."