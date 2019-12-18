#!/bin/bash
set -e

ROOT_DIR=$1
GIT=$2
REV=$3
NPROC=$4

#mkdir -p $ROOT_DIR
cd $ROOT_DIR
LOG_DIR=$ROOT_DIR/logs
mkdir $LOG_DIR
GIT_LOG=$LOG_DIR/git.log
MAKE_LOG=$LOG_DIR/make.log
TVM_DIR=$ROOT_DIR/tvm

START_TIME=$(python -c "import time; print(time.time())")
git clone --recursive $GIT $TVM_DIR 2>&1| tee $GIT_LOG
cd $TVM_DIR
git reset --hard $REV 2>&1| tee -a $GIT_LOG
python -c "import time,datetime; print(datetime.timedelta(seconds=time.time()-$START_TIME))" >> $GIT_LOG
BUILD_DIR=$TVM_DIR/build
mkdir $BUILD_DIR
cd $BUILD_DIR
cp $TVM_DIR/cmake/config.cmake $BUILD_DIR

echo "set(USE_LLVM ON)" >> config.cmake
echo "set(USE_ANTLR ON)" >> config.cmake
echo "set(CMAKE_CXX_FLAGS -Werror)" >> config.cmake
START_TIME=$(python -c "import time; print(time.time())")
cmake $TVM_DIR 2>&1| tee $LOG_DIR/cmake.log
make -j $NPROC 2>&1| tee $MAKE_LOG
python -c "import time,datetime; print(datetime.timedelta(seconds=time.time()-$START_TIME))" >> $MAKE_LOG