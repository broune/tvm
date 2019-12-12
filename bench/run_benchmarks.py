from collections import namedtuple
import typing
import tempfile, os, time, docker, datetime
from functools import partial
from multiprocessing import cpu_count as ncpu
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



def build_tvm(tvm_build_config : BuildConfig):
    """
    Compiles TVM.
    We are assuming this runs inside a docker.
    """
    client = docker.DockerClient(timeout=3600)
    runner = os.path.join("/runner", os.path.basename(tvm_build_config.runner))
    docker_output_path = "/op"
    root_dir = os.path.abspath('./tvm_builds/')
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)
    local_output_path = tempfile.mkdtemp(dir = root_dir)
    runner_cmd = " ".join([runner,docker_output_path, tvm_build_config.git_repo, tvm_build_config.git_revision, str(ncpu()),
                                         tvm_build_config.runner_params])
    container = client.containers.run(image=tvm_build_config.docker, 
                                        mounts=[docker.types.Mount(runner, tvm_build_config.runner, 'bind', True),
                                                docker.types.Mount(docker_output_path, local_output_path, 'bind', False),],
                                        command = runner_cmd,
                                        auto_remove=True)
    return BuildResult(config = tvm_build_config,
                            binaries = None,        #Need to figure out why just pointing to the build directory is not good enough.
                            logs = None,
                            metrics = None)

NeoBuildConfig = partial(BuildConfig, 'https://github.com/neo-ai/tvm.git')
NeoLatestBuildConfig = partial(NeoBuildConfig, 'HEAD')
NeoLatestCpuBuildConfig = partial(NeoLatestBuildConfig, 'tvmai/ci-cpu:latest')
ApacheBuildConfig = partial(BuildConfig, 'https://github.com/apache/incubator-tvm.git')
ApacheLatestBuildConfig = partial(ApacheBuildConfig, 'HEAD')
ApacheLatestCpuBuildConfig = partial(ApacheLatestBuildConfig, 'tvmai/ci-cpu:latest')


def run_main():
    # TODO: System for gathering available benchmarks and using the command
    # line and the local TVM to figure out which of them to run.

    build_config = NeoLatestCpuBuildConfig()
    build_result = build_tvm(build_config)

    benchmark_config = BenchmarkConfig()
    benchmark_result = run_benchmark(benchmark_config)

    benchmark_result_set = BenchmarkResultSet(build_result, [benchmark_result])
    compare_benchmarks(benchmark_result_set, [benchmark_result_set],
                       ["tvm_build_time", "model_compile_time", "run_time", "code size"])

    
if __name__ == "__main__":
    run_main()
