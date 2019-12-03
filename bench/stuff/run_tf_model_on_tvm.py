#!/usr/bin/env python
import numpy
import sys
import time
import tvm
from tvm import relay
from tvm.relay.frontend.tensorflow_parser import TFParser

if len(sys.argv) != 2:
    print("Need to supply one argument that is the path of a model directory.")
    exit(1)

model_dir = sys.argv[1]
run_count = 10

print("Loading and parsing TF model at", model_dir)
parser = TFParser(model_dir) 
graph_def = parser.parse()

print("Converting TF model to Relay")
mod, params = tvm.relay.frontend.from_tensorflow(graph_def)

print("Compiling to Relay VM")
compiler = tvm.relay.vm.VMCompiler()
ctx = tvm.cpu()
target = 'llvm -mcpu=skylake-avx512'
with tvm.relay.build_config(opt_level=3):
    vm = compiler.compile(mod, target)
vm.init(ctx)
vm.load_params(params)

print("Generating data and running model", run_count, "times")
data = numpy.random.rand(1, 3, 224, 224).astype('float32')
start = time.time()
for i in range(run_count):
    res = vm.invoke("main", [data])
end = time.time()

print("Time taken per iteration:", (end-start)/run_count * 1000)
