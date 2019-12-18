from collections import namedtuple
import typing, boto3
import tempfile, os, time, docker, datetime
from functools import partial
from multiprocessing import cpu_count as ncpu
from argparse import ArgumentParser

# Initial draft proposal for steps to be taken.
#
# TODO: This all assumes that we are running TVM, but we also want to be able
# for the baseline to be non-TVM. There should be an option for that.
#
# TODO: I'm tempted to make this just a hermetic and pure system that looks
# more like map-reduce with minimal structure to the tasks, though it's
# probably overkill for right now. Though maybe there would be a good existing
# system that already does this that we could use.


class BuildConfig:
    def __init__(self, git_repo, git_revision, docker, runner=os.path.abspath("build_tvm.sh"), runner_params=""):
        """
        # Path or URL to the git repository to get TVM from.
        git_repo: string

        # The git revision to compile.
        git_revision: str

        # The docker image to compile inside of.
        docker: str

        # Path or URL of a runner (be it a script or binary) to run inside the
        # container to build TVM.
        runner: str

        # The command line parameter(s) to pass to the runner.
        runner_params: str
        """
        self.git_repo=git_repo
        self.git_revision=git_revision
        self.docker=docker
        self.runner=runner
        self.runner_params=runner_params


class BuildResult:
    def __init__(self, config, binaries, logs, metrics):
        """
        # The config that was used to produce this result.
        config: BuildConfig
        
        # Path or URL to tar.gz file with binaries produced from building TVM.
        binaries: str

        # Path or URL to file containing logs produced from building TVM.
        logs: str

        # Path or URL to file containing metrics produced from building TVM.
        metrics: str
        """
        self.config = config
        self.binaries = binaries
        self.logs = logs
        self.metrics = metrics



def build_tvm(docker_client, local_output_path, tvm_build_config : BuildConfig):
    """
    Compiles TVM inside a docker and dumps the build directory.
    Loki: Copy runner inside RW mount dir or mount runner as RO ?
    """
    runner = os.path.join("/runner", os.path.basename(tvm_build_config.runner))
    docker_workspace = "/workspace"
    runner_cmd = " ".join([runner,docker_workspace, tvm_build_config.git_repo, tvm_build_config.git_revision, str(ncpu()),
                                         tvm_build_config.runner_params])
    logs = docker_client.containers.run(image=tvm_build_config.docker, 
                                        mounts=[docker.types.Mount(runner, tvm_build_config.runner, 'bind', True),
                                                docker.types.Mount(docker_workspace, local_output_path, 'bind', False),],
                                        command = runner_cmd,
                                        auto_remove=True)
    return BuildResult(config = tvm_build_config,
                            binaries = os.path.join(local_output_path, "tvm", "build"),        
                            logs = os.path.join(local_output_path,"logs"),
                            metrics = None)

NeoBuildConfig = partial(BuildConfig, 'https://github.com/neo-ai/tvm.git')
NeoLatestBuildConfig = partial(NeoBuildConfig, 'HEAD')
NeoLatestCpuBuildConfig = partial(NeoLatestBuildConfig, 'tvmai/ci-cpu:latest')
ApacheBuildConfig = partial(BuildConfig, 'https://github.com/apache/incubator-tvm.git')
ApacheLatestBuildConfig = partial(ApacheBuildConfig, 'HEAD')
ApacheLatestCpuBuildConfig = partial(ApacheLatestBuildConfig, 'tvmai/ci-cpu:latest')


class BenchmarkConfig:
    def __init__(self, name, docker, model_files, input_files={}, runner=os.path.abspath("./inference.py"), runner_params=""):
        """
        # The name of the benchmark.
        name: str

        # The docker image to run the benchmark inside of.
        docker: str

        # Input/Model files that will be made available inside of the container. The key
        # is the path or URL of a file and the value is the relative path inside of
        # the container that the file will be available at. S3 URLs are expected to be of the format s3://bucket/key. These files will be
        # read-only.
        input_files: typing.Dict[str, str]  
        model_files: typing.Dict[str, str]  

        # Path or URL of a runner (be it a script or binary) to run inside the
        # container to run the benchmark.
        runner: str

        # The command line parameter(s) to pass to the runner.
        runner_params: str
        """
        self.name=name
        self.docker=docker
        self.input_files=self.parse_file_list(input_files)
        self.model_files=self.parse_file_list(model_files)
        self.runner=runner
        self.runner_params=runner_params
        
    
    def parse_file_list(self, file_dict):
        temp_path = os.path.abspath('./temp/')
        download_initalized = False
        for local_file in file_dict:
            if not local_file.startswith('/'):
                _docker_file, _local_file = file_dict[local_file], local_file
                del file_dict[local_file]
                if _local_file.startswith('s3:'):
                    if not download_initalized:
                        try:
                            os.makedirs(temp_path)
                        except:
                            pass
                        import boto3
                        s3 = boto3.resource('s3', region_name='us-west-2')
                        download_initalized=True
                    link = _local_file.split('/')
                    bucket, key, local_file = link[2], "/".join(link[3:]), os.path.join(temp_path, link[-1])
                    s3.Bucket(bucket).download_file(key, local_file)
                    file_dict[local_file] = _docker_file
                else:
                    file_dict[os.path.abspath(_local_file)] = _docker_file
        return file_dict

ToyBenchmarkConfig = partial(BenchmarkConfig, 'ToyBenchmark')
ToyCpuBenchmarkConfig = partial(ToyBenchmarkConfig, 'tvmai/ci-cpu:latest')
ToyMobilenetCpuBenchmarkConfig = partial(ToyCpuBenchmarkConfig, {'s3://loki-benchmark-1/tf_slim_imagenet_classifier/mobilenet_v1_0.25_128.tar.gz':'/models/mobilenet_v1_0.25_128.tar.gz'})
ToySqueezenetCpuBenchmarkConfig = partial(ToyCpuBenchmarkConfig, {'s3://loki-benchmark-1/tf_slim_imagenet_classifier/squeezenet.tar.gz':'/models/squeezenet.tar.gz'})
ToyResnetCpuBenchmarkConfig = partial(ToyCpuBenchmarkConfig, {'s3://loki-benchmark-1/tf_slim_imagenet_classifier/resnet_v1_50.tar.gz':'/models/resnet_v1_50.tar.gz'})

class BenchmarkResult:
    def __init__(self, config, logs, metrics):
        """
        # The config that was used to produce this result.
        config : BenchmarkConfig
        
        # Path or URL to file containing logs produced from running the benchmark.
        logs: str

        # Path or URL to file containing metrics produced from running the benchmark.
        metrics: str
        """
        self.config=config
        self.logs=logs
        self.metrics=metrics


def run_benchmark(docker_client, tvm, local_output_path, benchmark_config : BenchmarkConfig):
    """
    Runs the benchmark inside a docker.
    """
    runner = os.path.join("/runner", os.path.basename(benchmark_config.runner))
    docker_workspace = "/workspace"
    log = os.path.join("benchmark.log")
    models = ",".join([str(m) for m in benchmark_config.model_files.values()])
    runner_cmd = "{} --model_dir {} --log {}".format(runner, models, os.path.join(docker_workspace, log))
    logs = docker_client.containers.run(image=benchmark_config.docker, 
                                        mounts=[docker.types.Mount(runner, benchmark_config.runner, 'bind', True),
                                                docker.types.Mount('/tvm', tvm, 'bind', True),
                                                docker.types.Mount(docker_workspace, local_output_path, 'bind', True),]+\
                                        [ docker.types.Mount(benchmark_config.input_files[key], key, 'bind', False) for key in benchmark_config.input_files]+\
                                        [ docker.types.Mount(benchmark_config.model_files[key], key, 'bind', False) for key in benchmark_config.model_files],
                                        command = runner_cmd,
                                        stdout=True, stderr=True,
                                        auto_remove=True,
                                        environment={'TVM_HOME':'/tvm',
                                                    'PYTHONPATH':'/tvm/python:/tvm/topi/python:/tvm/nnvm/python',},)

    return BenchmarkResult(config = benchmark_config, 
                            logs = os.path.join(local_output_path, log),
                            metrics = None)


def run_main(build_dir, bench_dir):
    # TODO: System for gathering available benchmarks and using the command
    # line and the local TVM to figure out which of them to run.
    client = docker.DockerClient()  


    build_config = NeoLatestCpuBuildConfig()
    build_output_path = tempfile.mkdtemp(dir = build_dir, prefix = build_config.git_revision+'_')
    build_result = build_tvm(client, build_output_path, build_config)

    benchmark_config = ToyResnetCpuBenchmarkConfig()
    bench_output_path = tempfile.mkdtemp(dir = bench_dir, prefix = benchmark_config.name+'_')
    benchmark_result = run_benchmark(client, os.path.join(build_output_path, "tvm"), bench_output_path, benchmark_config)

    benchmark_result_set = BenchmarkResultSet(build_reslt, [benchmark_result])
    compare_benchmarks(benchmark_result_set, [benchmark_result_set],
                       ["tvm_build_time", "model_compile_time", "run_time", "code size"])

    
if __name__ == "__main__":
    parser = ArgumentParser(description='Benchmark your changes to TVM.')
    parser.add_argument('--out', type=str, help='Path to output directory. If it doesnt exist, it will be created.', default='.')
    args = parser.parse_args()
    
    root_dir = os.path.abspath(args.out)
    build_dir = os.path.join(root_dir, 'tvm_builds')
    bench_dir = os.path.join(root_dir, 'benchmarks')
    for d in [build_dir,bench_dir]:
        try:
            os.makedirs(d)
        except:
            pass

    run_main(build_dir, bench_dir)
