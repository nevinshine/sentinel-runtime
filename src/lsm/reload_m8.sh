#!/bin/bash
# reload_m8.sh - Automated Sentinel Reset & Test

echo "🔴 Killing old Sentinel instance..."
sudo pkill -9 -f sentinel_loader
# Kill any stale trace pipe readers
sudo pkill -f "cat /sys/kernel/debug/tracing/trace_pipe"
sudo rm -rf /sys/fs/bpf/sentinel_maps

echo "🔨 Building Sentinel M8.1..."
clang -g -O2 -Wall -target bpf -D__TARGET_ARCH_x86_64 -Iheaders -c sentinel_lsm.c -o sentinel_lsm.bpf.o
clang -g -O2 -Wall -o sentinel_loader sentinel_loader.c -lbpf -lelf -lz

if [ ! -f sentinel_lsm.bpf.o ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "🟢 Starting New Sentinel Engine..."
sudo ./sentinel_loader > sentinel.log 2>&1 &
LOADER_PID=$!
sleep 2

if ! ps -p $LOADER_PID > /dev/null; then
    echo "❌ Sentinel failed to start! Check sentinel.log:"
    cat sentinel.log
    exit 1
fi

echo "🛡️  Engine Active. PID: $LOADER_PID"
echo "---------------------------------------------------"
echo "✅ SENTINEL RELOADED SUCCESSFULLY"
echo ""
echo "👉 NOW RUN THESE COMMANDS TO TEST:"
echo "   sudo ./sentinel_loader mark \$\$"
echo "   /usr/bin/ping -c 1 8.8.8.8"
echo "---------------------------------------------------"


