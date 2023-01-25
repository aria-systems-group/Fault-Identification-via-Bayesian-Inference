import sys
import os
import getopt # command line parsing
from src.TestManager import TestManager


def cmd_parser(argv):
	simDir = ''
	truthFile = ''
	opts, args = getopt.getopt(argv,"hs:t:",["simulations=","truth="])
	for opt, arg in opts:
		if opt == '-h':
			print ('test.py -s <path/to/simulations/> -t <path/to/truth/telemetry.csv>')
			sys.exit()
		elif opt in ("-s", "--simulations"):
			simDir = arg
		elif opt in ("-t", "--truth"):
			truthFile = arg
	
	# make sure that the paths exists
	assert os.path.exists(simDir), "The path to the simulation database does not exist."
	assert os.path.isfile(truthFile), "The path to the telemetry data does not exist."
	return simDir, truthFile

if __name__ == '__main__':
	path2sim, path2telem = cmd_parser(sys.argv[1:])
	# initialize a test manager for fault ID
	tester = TestManager(path2sim, path2telem)
	# run fault ID
	tester.run_offline_fault_ID()


