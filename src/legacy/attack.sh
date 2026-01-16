#!/bin/bash
# attack.sh - Compiles and runs the simulation

# 1. Compile (Quietly)
gcc threat.c -o threat

# 2. Run
./threat

# 3. Cleanup
rm threat
