# Sentinel M5 - eBPF LSM Engine Build

CLANG ?= clang
LLVM_STRIP ?= llvm-strip
BPFTOOL ?= bpftool

# Kernel Arch
ARCH := $(shell uname -m)
CFLAGS_BPF := -g -O2 -Wall -Werror -target bpf -D__TARGET_ARCH_$(ARCH) -Iheaders
CFLAGS_USER := -g -O2 -Wall -Werror

# Targets
BPF_OBJ := sentinel_lsm.bpf.o
LOADER := sentinel_loader

.PHONY: all clean

all: $(BPF_OBJ) $(LOADER)

# 1. Build the BPF Kernel Object
$(BPF_OBJ): sentinel_lsm.c headers/vmlinux.h
	$(CLANG) $(CFLAGS_BPF) -c sentinel_lsm.c -o $@
	$(LLVM_STRIP) -g $@

# 2. Build the Userspace Loader (Links against libbpf)
$(LOADER): sentinel_loader.c
	$(CLANG) $(CFLAGS_USER) -o $@ sentinel_loader.c -lbpf -lelf -lz

# 3. Build the Dashboard
tests/sentinel_top: tests/sentinel_top.c
	$(CC) $(CFLAGS_USER) -o $@ $< -lpthread

clean:
	rm -f *.o $(LOADER) tests/sentinel_top