
import numpy as np
import tvm
from tvm import relay
import gluon

def load_mx():
    import mxnet
    from mxnet.gluon.model_zoo import vision
    model = vision.get_model("resnet18_v1", pretrained=True)
    mod, params = tvm.relay.frontend.from_mxnet(model, shape={'data':(1,3,224,224)})
    return mod, params    

mod, params = load_mx()
compiler = tvm.relay.vm.VMCompiler()
ctx = tvm.cpu()
target = 'llvm -mcpu=skylake-avx512'
with relay.build_config(opt_level=3):
    vm = compiler.compile(mod, target)
vm.init(ctx)
vm.load_params(params)

data = np.random.rand(1, 3, 224, 224).astype('float32')
import time
nums = 10
start = time.time()
for i in range(nums):
    res = vm.invoke("main", [data])
end = time.time()

print((end-start)/nums * 1000)
