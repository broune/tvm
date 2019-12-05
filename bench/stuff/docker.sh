#!/bin/bash			
set -e -x

TVM_DIR=$1
BENCH_DIR=$TVM_DIR/bench			#You need to create these directories if they dont exist !
OUTPUT_DIR=$TVM_DIR/docker_op
PATCH_DIR=$TVM_DIR/patches

docker run --rm \
--mount type=bind,source="$BENCH_DIR",target=/code \
--mount type=bind,source="$OUTPUT_DIR",target=/op \
--mount type=bind,source="$PATCH_DIR",target=/patches \
tvmai/ci-cpu:latest bash /code/stuff/docker_entry_trigger.sh

#This script is for development and testing only. Docker has a pretty good Python SDK. Should launch the docker from the run_benhcmark.py when its ready.