# Sentinel Runtime M4 Makefile (Seccomp Architecture)
CC = gcc
# [FIX 1] Added -lseccomp to link against the Seccomp library
CFLAGS = -Wall -O2 -I./src/engine
LDFLAGS = -lseccomp

TARGET = bin/sentinel

# Define Test Sources
TEST_SRC_1 = tests/evasion/recursive_fork.c
TEST_SRC_2 = tests/evasion/dup_test.c

all: clean sentinel recursive_fork dup_test

# [FIX 2] Removed pidmap.c (M4 uses Seccomp for state, not ptrace maps)
sentinel: src/engine/main.c src/engine/logger.c src/engine/fdmap.c
	@mkdir -p bin
	@echo "[BUILD] Compiling Sentinel M4 (Seccomp Architecture)..."
	$(CC) $(CFLAGS) -o $(TARGET) src/engine/main.c src/engine/logger.c src/engine/fdmap.c $(LDFLAGS)

recursive_fork: $(TEST_SRC_1)
	@mkdir -p bin
	$(CC) -o bin/recursive_fork $(TEST_SRC_1)

dup_test: $(TEST_SRC_2)
	@mkdir -p bin
	$(CC) -o bin/dup_test $(TEST_SRC_2)

clean:
	@rm -rf bin/*
	@echo "[CLEAN] Artifacts removed."
