from collections import namedtuple
import typing

# Initial draft proposal for steps to be taken.
#
# TODO: This all assumes that we are running TVM, but we also want to be able
# for the baseline to be non-TVM. There should be an option for that.
#
# TODO: I'm tempted to make this just a hermetic and pure system that looks
# more like map-reduce with minimal structure to the tasks, though it's
# probably overkill for right now. Though maybe there would be a good existing
# system that already does this that we could use.


@dataclass
class BuildConfig:
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


@dataclass
class BuildResult:
    # The config that was used to produce this result.
    config: BuildConfig
    
    # Path or URL to tar.gz file with binaries produced from building TVM.
    binaries: str

    # Path or URL to file containing logs produced from building TVM.
    logs: str

    # Path or URL to file containing metrics produced from building TVM.
    metrics: str


def build_tvm(tvm_build_config : TVMBuildConfig):
    """Compiles TVM."""
    # TODO: Build TVM.
    return TVMBuildResult(binaries = "foo/bar/baz.tar.gz")


@dataclass
class BenchmarkConfig:
    # The name of the benchmark.
    name: str

    # The docker image to run the benchmark inside of.
    docker: str

    # Input files that will be made available inside of the container. The key
    # is the path or URL of a file and the value is the relative path inside of
    # the container that the file will be available at. These files will be
    # read-only.
    input_files: typing.Dict[str, str]

    # Path or URL of a runner (be it a script or binary) to run inside the
    # container to run the benchmark.
    runner: str

    # The command line parameter(s) to pass to the runner.
    runner_params: str


@dataclass
class BenchmarkResult:
    # The config that was used to produce this result.
    config : BenchmarkConfig
    
    # Path or URL to file containing logs produced from running the benchmark.
    logs: str

    # Path or URL to file containing metrics produced from running the benchmark.
    metrics: str


def run_benchmark(benchmark_config : BenchmarkConfig):
    # TODO: run the benchmark
    return BenchmarkResult(metrics = "foo/bar/baz.json")


@dataclass
class BenchmarkResultSet:
    # The build result for building TVM.
    build_result : BuildResult

    # The results of running the benchmarks.
    benchmark_result : typing.List[BenchmarkResult]


def compare_benchmarks(baseline : BenchmarkResultSet, result_sets : typing.List[BenchmarkResultSet], metrics : typing.List[str]):
    # TODO: show a comparison of base and result_sets across the given named metrics.
    pass


def run_main():
    # TODO: System for gathering available benchmarks and using the command
    # line and the local TVM to figure out which of them to run.

    build_config = BuildConfig()
    build_result = build_tvm(build_config)

    benchmark_config = BenchmarkConfig()
    benchmark_result = run_benchmark(benchmark_config)

    benchmark_result_set = BenchmarkResultSet(build_result, [benchmark_result])
    compare_benchmarks(benchmark_result_set, [benchmark_result_set],
                       ["tvm_build_time", "model_compile_time", "run_time", "code size"])

    
if name == "__main__":
    run_main()
