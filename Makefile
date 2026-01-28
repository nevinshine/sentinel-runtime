CC = gcc
CFLAGS = -Wall -O2 -I./src/engine
TARGET = bin/sentinel

# Define Test Sources
TEST_SRC_1 = tests/evasion/recursive_fork.c
TEST_SRC_2 = tests/evasion/dup_test.c

all: clean build

build:
	@mkdir -p bin
	@echo "[BUILD] Compiling Sentinel Engine (M3.2)..."
	$(CC) $(CFLAGS) -o $(TARGET) src/engine/main.c src/engine/logger.c

	@echo "[BUILD] Compiling Tests..."
	$(CC) -o bin/recursive_fork $(TEST_SRC_1)
	$(CC) -o bin/dup_test $(TEST_SRC_2)



# Add to your Makefile
all: sentinel dup_test

dup_test: tests/evasion/dup_test.c
	gcc -o bin/dup_test tests/evasion/dup_test.c

clean:
	@rm -rf bin/*