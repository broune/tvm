#!/bin/bash
set -e

OUTPUT_DIR=$1
GIT=$2
REV=$3
GIT_LOG=$OUTPUT_DIR/git.log
mkdir -p $OUTPUT_DIR
START_TIME=$(python -c "import time; print(time.time())")
git clone --recursive $GIT /tvm 2>&1| tee $GIT_LOG
cd /tvm
git reset --hard $REV 2>&1| tee -a $GIT_LOG
python -c "import time,datetime; print(datetime.timedelta(seconds=time.time()-$START_TIME))" >> $GIT_LOG
cd $OUTPUT_DIR
cp /tvm/cmake/config.cmake .

#echo "set(USE_LLVM ON)" >> config.cmake
#echo "set(USE_ANTLR ON)" >> config.cmake
#echo "set(CMAKE_CXX_FLAGS -Werror)" >> config.cmake
START_TIME=$(python -c "import time; print(time.time())")
cmake /tvm 2>&1| tee cmake.log
make -j $4 2>&1| tee make.log
python -c "import time,datetime; print(datetime.timedelta(seconds=time.time()-$START_TIME))" >> make.log
mkdir -p export/
cp *.log export/
cp *.so export/
