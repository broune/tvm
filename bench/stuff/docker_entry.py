import os,time


if __name__=="__main__":
	start_time=time.time()
	os.system("make -j16 > compile.log") #Maybe take num threads as an input ?
	time_taken = time.time()-start_time
	log = "Compilation finished in {} seconds...".format(time_taken)
	print(log)
	os.system("echo {} >> compile.log".format(log))
