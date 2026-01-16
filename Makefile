CC = gcc
CFLAGS = -Wall -O2 -I./src/engine
TARGET = bin/sentinel
TEST_TARGET = bin/recursive_fork

SRC = src/engine/main.c src/engine/logger.c
TEST_SRC = tests/evasion/recursive_fork.c

all: clean build

build:
	@mkdir -p bin
	@echo "[BUILD] Compiling Sentinel Engine (M2.0)..."
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)
	@echo "[BUILD] Compiling Evasion Test..."
	$(CC) -o $(TEST_TARGET) $(TEST_SRC)

clean:
	@rm -rf bin/*
