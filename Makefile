CC = gcc
CFLAGS = -Wall -O2 -I./src/engine
TARGET = bin/sentinel

# Define Test Sources
TEST_SRC_1 = tests/evasion/recursive_fork.c
TEST_SRC_2 = tests/evasion/dup_test.c

all: sentinel recursive_fork dup_test

sentinel: src/engine/main.c src/engine/logger.c src/engine/fdmap.c
	@mkdir -p bin
	@echo "[BUILD] Compiling Sentinel Engine (M3.2)..."
	$(CC) $(CFLAGS) -o $(TARGET) src/engine/main.c src/engine/logger.c src/engine/fdmap.c

recursive_fork: $(TEST_SRC_1)
	@mkdir -p bin
	$(CC) -o bin/recursive_fork $(TEST_SRC_1)

dup_test: $(TEST_SRC_2)
	@mkdir -p bin
	$(CC) -o bin/dup_test $(TEST_SRC_2)


clean:
	@rm -rf bin/*