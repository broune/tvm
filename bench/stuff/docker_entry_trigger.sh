#!/bin/bash
set -e

# We are only using a bash script here because git does not have a reliable python sdk.
GIT=https://github.com/neo-ai/tvm.git
REV=HEAD
git clone --recursive $GIT /tvm 2>&1| tee /op/git.log
cd /tvm
git reset --hard $REV 2>&1| tee -a /op/git.log
#Patch files correspond to git stashes.
if test "$(ls /patches/)"; then
	git apply /patches/* 2>&1| tee -a /op/git.log	
fi

#What happens if we need to recompile tvm ? Maybe add a random directory inside build ?
mkdir -p /op/build && cd /op/build
# Technically we want to let the user specify these options. copy their own config.cmake file ?
cp /tvm/cmake/config.cmake .
echo "set(USE_LLVM ON)" >> config.cmake
echo "set(USE_ANTLR ON)" >> config.cmake
echo "set(CMAKE_CXX_FLAGS -Werror)" >> config.cmake
cmake /tvm 2>&1| tee cmake.log			

python3 /code/stuff/docker_entry.py