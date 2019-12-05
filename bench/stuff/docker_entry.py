import os,time            #If you want to do more compilicated stuff, switch to subprocess.call
from argparse import ArgumentParser


def compileTVM(num_threads, compilation_log):
    start_time=time.time()
    print("Compiling TVM...")
    exit_status = os.system("make -j{} 2>&1| tee {}".format(num_threads, compilation_log)) 
    time_taken = time.time()-start_time
    log_msg = "Compilation FAILED" if exit_status else "Compilation finished"
    log_msg += " in {:.2f} mins... Log resides at {} ".format(time_taken/60, os.path.join(os.getcwd(),compilation_log))
    print(log_msg)
    os.system("echo {} >> {}".format(log_msg, compilation_log))

if __name__=="__main__":
    parser = ArgumentParser(description='Launching a python docker entrypoint to do complicated tasks like building TVM')
    parser.add_argument('--log', type=str, help='Name for the compilation log', default='compile.log')
    parser.add_argument('--num_threads', type=int, help='Number of threads to speed up make', default='16')
    args = parser.parse_args()

    compileTVM(args.num_threads, args.log)  