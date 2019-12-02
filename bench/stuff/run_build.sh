#!/bin/bash
set -e

cd ~
tar -xf /bench/tvm.tar.gz

mkdir -p tvm/build
cd tvm/build
cp ../cmake/config.cmake .
echo "set(USE_LLVM ON)" >> config.cmake
echo "set(USE_ANTLR ON)" >> config.cmake
echo "set(CMAKE_CXX_FLAGS -Werror)" >> config.cmake
cmake ..

export TIMEFORMAT=%R
{ time make -j16 2>&1 1>/bench/logs; } 2> /bench/compile_time






