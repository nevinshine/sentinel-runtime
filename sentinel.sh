#!/bin/bash

# ==========================================
# SENTINEL RUNTIME ORCHESTRATOR (v1.2)
# ==========================================

PIPE_REQ="/tmp/sentinel_req"
PIPE_RESP="/tmp/sentinel_resp"
BRAIN_LOG="brain_debug.log"

# Function to clean up background processes on exit
cleanup() {
    echo ""
    echo "[ORCHESTRATOR] 🛑 Shutting down Neural Cortex..."
    if [ -n "$BRAIN_PID" ]; then
        kill "$BRAIN_PID" 2>/dev/null
    fi
    rm -f "$PIPE_REQ" "$PIPE_RESP"
    echo "[ORCHESTRATOR] 🧹 Cleanup complete."
    exit
}

# Trap Ctrl+C (SIGINT) to ensure cleanup
trap cleanup SIGINT SIGTERM

echo "[ORCHESTRATOR] 🚀 Initializing Sentinel Platform..."

# 1. Clear old artifacts
rm -f "$PIPE_REQ" "$PIPE_RESP"

# 2. Start the Brain (Hidden)
# We redirect logs to a file so they don't clutter the screen
echo "[ORCHESTRATOR] 🧠 Booting WiSARD Engine..."
python3 analysis/bridge.py > "$BRAIN_LOG" 2>&1 &
BRAIN_PID=$!

# 3. Wait for the Brain to create the pipes (Health Check)
TIMEOUT=0
while [[ ! -p "$PIPE_REQ" || ! -p "$PIPE_RESP" ]]; do
    sleep 0.1
    TIMEOUT=$((TIMEOUT+1))
    if [ $TIMEOUT -ge 50 ]; then
        echo "[ERROR] Brain failed to start. Check $BRAIN_LOG"
        cleanup
    fi
done

echo "[ORCHESTRATOR] 🔗 Neural Link Established (PID: $BRAIN_PID)."
echo "[ORCHESTRATOR] 🛡️  Engaging Kinetic Defense..."
echo "---------------------------------------------------"

# 4. Run the C Engine (Foreground)
# We pass all arguments ($@) directly to the C binary
./sentinel "$@"

# 5. Normal Exit
cleanup
