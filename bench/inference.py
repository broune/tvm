#!/usr/bin/env python3
import numpy, sys, time, datetime, tvm, logging, os, tarfile, subprocess
from argparse import ArgumentParser

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def extract(src_path):
    # Extract model file
    dst_path = src_path[:-src_path[::-1].index('/')]
    tar = tarfile.open(src_path, "r:gz")
    tar.extractall(path=dst_path)
    tar.close()
    for root,dirs,files in os.walk(dst_path):
        for file in files:
            model = os.path.join(dst_path,file)
            os.rename(os.path.join(root,file), model)
            if ".pb" in model:
                logging.info("Extracting model from {} to {}".format(src_path, model))
                return model



if __name__=="__main__":
    parser = ArgumentParser(description='Launching a Benchmark inside a docker.')
    parser.add_argument('--model', type=str, help='Path to a model', required=True)
    parser.add_argument('--log', type=str, help='Path to write a log', required=True)
    parser.add_argument('--iterations', type=int, help='Number of iterations', default=10)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO, filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    logging.info("Loading and parsing TF model at {}".format(args.model))
    if args.model.endswith('tar.gz'):
        args.model=extract(args.model)
    
    install("tensorflow")
    from tvm import relay
    from tvm.relay.frontend.tensorflow_parser import TFParser
    from tvm.relay.backend.vm import VirtualMachine, compile
    parser = TFParser(args.model) 
    graph_def = parser.parse()

    logging.info("Converting TF model to Relay")
    mod, params = tvm.relay.frontend.from_tensorflow(graph_def)

    logging.info("Compiling to Relay VM")
    ctx = tvm.cpu()
    target = 'llvm -mcpu=skylake-avx512'
    vm=VirtualMachine(compile(mod, target, params=params))
    vm.init(ctx)

    logging.info("Generating data and running model {} times".format(args.iterations))
    data = numpy.random.rand(1, 3, 224, 224).astype('float32')
    start = time.time()
    for i in range(args.iterations):
        res = vm.run([data])
    end = time.time()

    logging.info("Time taken per iteration: {}ms".format((end-start)/args.iterations * 1000))
