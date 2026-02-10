#!/bin/bash
# test_jailbreak.sh - Automated Sentinel Penetration Test

echo "🛠️  Compiling Jailbreak Suite..."
gcc -o jailbreak tests/jailbreak.c -lpthread

if [ ! -f jailbreak ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

echo "🟢 Launching Victim Process (Background)..."
./jailbreak > pwn.log 2>&1 &
VICTIM_PID=$!

sleep 1

echo "💀 Arming Victim PID: $VICTIM_PID with Sentinel M8.2..."
sudo ./sentinel_loader mark $VICTIM_PID

echo "💥 TRIGGERING ATTACKS..."
# Send newline to stdin of background process? 
# Background process reads from stdin which is closed if backgrounded?
# Let's modify C code to not wait for input if argument provided.
# No, let's just send signal or use a pipe.

# Easier: Use "expect" or just modify C code to assume armed if arg "auto" is passed.
# Let's modify C code in next step.
# For now, kill it and restart with "auto" flag (I will add it).
kill -9 $VICTIM_PID 2>/dev/null

echo "🔄 Restarting in AUTO-ATTACK mode..."
./jailbreak auto > pwn.log 2>&1 &
VICTIM_PID=$!
sleep 1

echo "💀 RE-Arming Victim PID: $VICTIM_PID..."
sudo ./sentinel_loader mark $VICTIM_PID

echo "⏳ Waiting for Carnage..."
sleep 2

# Stop trace capture
sudo kill $TRACE_PID 2>/dev/null

echo "📜 ATTACK REPORT (pwn.log):"
echo "---------------------------------------------------"
cat pwn.log
echo "---------------------------------------------------"
echo "🛡️  SENTINEL KERNEL LOGS:"
echo "---------------------------------------------------"
echo "Check your other terminal where you ran 'trace_pipe'!"
echo "You should see 'Sentinel: BLOCKED EXEC' messages."
echo "---------------------------------------------------"
echo "✅ PENETRATION TEST COMPLETE."
