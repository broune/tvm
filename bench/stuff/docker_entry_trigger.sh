#!/bin/bash
set -e

# We need the ability to specify apache/neo-ai TVM
git clone --recursive https://github.com/neo-ai/tvm.git
cd tvm
# The patch needs to come from outside. Each patch file is basically a git stash. We need this to be mounted inside the docker.
git apply patches/*
#What happens if we need to recompile tvm ? Maybe add a random directory inside build ?
mkdir build && cd build

# Technically we want to let the user specify these options. copy their own config.cmake file ?
cp ../cmake/config.cmake .
echo "set(USE_LLVM ON)" >> config.cmake
echo "set(USE_ANTLR ON)" >> config.cmake
echo "set(CMAKE_CXX_FLAGS -Werror)" >> config.cmake
cmake ..

python3 docker_entry.py