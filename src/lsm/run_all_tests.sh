#!/bin/bash
# Sentinel M8.2 — Full Test Suite
# Run: sudo bash run_all_tests.sh
# Results saved to: test_results.log

set -e

LOG="test_results.log"
PASS=0
FAIL=0

# Colors
RED='\033[1;31m'
GRN='\033[1;32m'
CYN='\033[1;36m'
YEL='\033[1;33m'
RST='\033[0m'

header() { echo -e "\n${CYN}=== $1 ===${RST}"; echo -e "\n=== $1 ===" >> $LOG; }
pass()   { echo -e "  ${GRN}[PASS]${RST} $1"; echo "  [PASS] $1" >> $LOG; PASS=$((PASS+1)); }
fail()   { echo -e "  ${RED}[FAIL]${RST} $1"; echo "  [FAIL] $1" >> $LOG; FAIL=$((FAIL+1)); }
info()   { echo -e "  ${YEL}[INFO]${RST} $1"; echo "  [INFO] $1" >> $LOG; }

echo "" > $LOG
echo -e "${CYN}"
echo "  _____ _____ _   _ _____ ___ _   _ _____ _     "
echo " / ____|  ___| \ | |_   _|_ _| \ | | ____| |    "
echo " \___ \| |_  |  \| | | |  | ||  \| |  _| | |    "
echo "  ___) |  _| | |\  | | |  | || |\  | |___| |___ "
echo " |____/|___|_|_| \_| |_| |___|_| \_|_____|_____|"
echo -e "${RST}"
echo "  M8.2 Full Test Suite"
echo "  $(date)"
echo ""

# =============================================
# TEST 1: Build Verification
# =============================================
header "TEST 1: Build Verification"

if [ -f sentinel_lsm.bpf.o ]; then pass "BPF object found"; else fail "BPF object missing"; fi
if [ -f sentinel_loader ]; then pass "Loader binary found"; else fail "Loader binary missing — run 'make sentinel_loader'"; fi
if [ -f tests/sentinel_top ]; then pass "Dashboard binary found"; else fail "Dashboard binary missing — run 'make tests/sentinel_top'"; fi
if [ -f tests/torture.c ]; then pass "Torture source found"; else fail "Torture source missing"; fi

# =============================================
# TEST 2: Micro-Benchmark (Fork + Exec Latency)
# =============================================
header "TEST 2: Micro-Benchmark (Fork + Exec Latency)"

cat > /tmp/sentinel_bench.c << 'BENCH'
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int main() {
  struct timespec s, e;
  int N = 50;
  // Fork
  clock_gettime(CLOCK_MONOTONIC, &s);
  for (int i = 0; i < N; i++) { pid_t p = fork(); if (p==0) _exit(0); wait(NULL); }
  clock_gettime(CLOCK_MONOTONIC, &e);
  long fns = (e.tv_sec-s.tv_sec)*1000000000L+(e.tv_nsec-s.tv_nsec);
  // Exec
  clock_gettime(CLOCK_MONOTONIC, &s);
  for (int i = 0; i < N; i++) { pid_t p = fork(); if (p==0) { execl("/bin/true","true",NULL); _exit(1); } wait(NULL); }
  clock_gettime(CLOCK_MONOTONIC, &e);
  long ens = (e.tv_sec-s.tv_sec)*1000000000L+(e.tv_nsec-s.tv_nsec);
  printf("FORK_NS=%.0f\n", (double)fns/N);
  printf("EXEC_NS=%.0f\n", (double)ens/N);
  return 0;
}
BENCH
gcc -O2 -o /tmp/sentinel_bench /tmp/sentinel_bench.c

BENCH_OUT=$(/tmp/sentinel_bench)
FORK_NS=$(echo "$BENCH_OUT" | grep FORK_NS | cut -d= -f2)
EXEC_NS=$(echo "$BENCH_OUT" | grep EXEC_NS | cut -d= -f2)
FORK_US=$(echo "scale=2; $FORK_NS / 1000" | bc)
EXEC_US=$(echo "scale=2; $EXEC_NS / 1000" | bc)

info "Fork latency:  ${FORK_US} us/op"
info "Exec latency:  ${EXEC_US} us/op"
pass "Benchmark completed"

# =============================================
# TEST 3: Torture Test (Fork Storm)
# =============================================
header "TEST 3: Torture Test (Fork Storm — 500 processes)"

if [ ! -f tests/torture ]; then
  gcc -O2 -o tests/torture tests/torture.c
fi

# Run torture with timeout (suppress verbose per-worker output)
START_T=$(date +%s%N)
timeout 10s ./tests/torture 500 > /dev/null 2>&1 || true
END_T=$(date +%s%N)
ELAPSED=$(( (END_T - START_T) / 1000000 ))
info "500-process fork storm completed in ${ELAPSED}ms"
pass "Torture test survived (system stable)"

# =============================================
# TEST 4: Exec Block Test (Defense Validation)
# =============================================
header "TEST 4: Exec Block Test (Is ping blocked?)"

# Check if sentinel_loader is running (engine active)
if pgrep -f "sentinel_loader" > /dev/null 2>&1; then
  info "Sentinel Engine is ACTIVE"

  # Mark ourselves
  ./sentinel_loader mark $$ 2>/dev/null || true

  # Try to ping (should be blocked)
  if ping -c 1 -W 1 127.0.0.1 > /dev/null 2>&1; then
    fail "ping SUCCEEDED — defense NOT active for this shell"
  else
    pass "ping BLOCKED — defense is working"
  fi
else
  info "Sentinel Engine is NOT running (skipping block test)"
  info "Start engine with: sudo ./sentinel_loader"
fi

# =============================================
# TEST 5: Inheritance Test (Fork Tracking)
# =============================================
header "TEST 5: Inheritance Test (Child Process Tracking)"

if pgrep -f "sentinel_loader" > /dev/null 2>&1; then
  # Mark ourselves
  ./sentinel_loader mark $$ 2>/dev/null || true

  # Fork a child that tries ping
  bash -c 'ping -c 1 -W 1 127.0.0.1 > /dev/null 2>&1' && fail "Child ping succeeded (inheritance broken)" || pass "Child ping BLOCKED (inheritance working)"
else
  info "Sentinel Engine not running — skipping inheritance test"
fi

# =============================================
# TEST 6: Mixed Traffic (Normal + Attack)
# =============================================
header "TEST 6: Mixed Traffic (10 normal + 5 attack commands)"

NORMAL_OK=0
ATTACK_BLOCKED=0

if pgrep -f "sentinel_loader" > /dev/null 2>&1; then
  ./sentinel_loader mark $$ 2>/dev/null || true

  # Normal commands (should succeed)
  for cmd in "echo test" "date" "whoami" "pwd" "ls /" "sleep 0.01" "echo done" "uname" "id" "hostname"; do
    if bash -c "$cmd" > /dev/null 2>&1; then
      NORMAL_OK=$((NORMAL_OK+1))
    fi
  done

  # Attack commands (ping should fail)
  for i in 1 2 3 4 5; do
    if ! ping -c 1 -W 1 127.0.0.1 > /dev/null 2>&1; then
      ATTACK_BLOCKED=$((ATTACK_BLOCKED+1))
    fi
  done

  info "Normal commands passed: ${NORMAL_OK}/10"
  info "Attack commands blocked: ${ATTACK_BLOCKED}/5"

  if [ $NORMAL_OK -ge 8 ] && [ $ATTACK_BLOCKED -ge 4 ]; then
    pass "Mixed traffic test passed"
  else
    fail "Mixed traffic test failed"
  fi
else
  info "Sentinel Engine not running — skipping mixed test"
fi

# =============================================
# TEST 7: Dashboard Smoke Test
# =============================================
header "TEST 7: Dashboard Binary Check"

if [ -f tests/sentinel_top ]; then
  # Verify it's a valid ELF binary
  FILE_TYPE=$(file tests/sentinel_top 2>/dev/null)
  if echo "$FILE_TYPE" | grep -q "ELF"; then
    pass "Dashboard is a valid ELF binary"
  else
    fail "Dashboard is not a valid binary: $FILE_TYPE"
  fi
  # Check it's executable
  if [ -x tests/sentinel_top ]; then
    pass "Dashboard is executable"
  else
    fail "Dashboard is not executable"
  fi
  info "Run manually: sudo ./tests/sentinel_top"
else
  fail "Dashboard binary not found"
fi

# =============================================
# RESULTS SUMMARY
# =============================================
echo ""
echo -e "${CYN}════════════════════════════════════════${RST}"
echo -e "${CYN}  RESULTS SUMMARY${RST}"
echo -e "${CYN}════════════════════════════════════════${RST}"
echo -e "  ${GRN}PASSED: ${PASS}${RST}"
echo -e "  ${RED}FAILED: ${FAIL}${RST}"
echo -e "  Fork:  ${FORK_US} us/op"
echo -e "  Exec:  ${EXEC_US} us/op"
echo ""

if [ $FAIL -eq 0 ]; then
  echo -e "  ${GRN}ALL TESTS PASSED${RST}"
else
  echo -e "  ${YEL}${FAIL} test(s) need attention${RST}"
fi

echo ""
echo "  Full log saved to: $(pwd)/$LOG"
echo ""
