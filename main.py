import sys
import os
import getopt # command line parsing
from typing import List, Tuple
from src.TestManager import TestManager


def cmd_parser(argv: List[str]) -> Tuple[str, str]:
	""" Parses the command line arguments.
	Keyword arguments:
	argv -- the list of all command line arguments
	
	Parses the command line arguments and returns a 
	tuple of strings (path_2_sim, path_2_telem) that point 
	to the digital twin simulations and the telemetry.csv 
	file, respectively, for a particular BSK truth simulation. 
	"""
	sim_dir_path = ''
	truth_csv_path = ''
	opts, args = getopt.getopt(argv,"hs:t:",["help","simulations=","truth="])
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print("Run the MBFID framework by typing one of the following:")
			print ('main.py --simulations <path/to/simulations> -truth <path/to/truth>/telemetry.csv')
			print ('main.py -s <path/to/simulations> -t <path/to/truth>/telemetry.csv')
			sys.exit()
		elif opt in ("-s", "--simulations"):
			sim_dir_path = arg
			if sim_dir_path[-1] != "/":
				sim_dir_path += "/"
		elif opt in ("-t", "--truth"):
			truth_csv_path = arg
	
	# make sure that the paths exists and point to meaningful data
	assert os.path.exists(sim_dir_path), "The path to the simulation database does not exist."
	assert os.path.isfile(truth_csv_path), "The path to the telemetry.csv file does not exist."
	return sim_dir_path, truth_csv_path

if __name__ == '__main__':
	# parse the command line
	''' This is the main script. It parses the command line 
	arguments, runs the MBFID framework, and exports the results.
	run main.py --help for more information on how to run the code
	''' 
	sim_dir_path, telem_csv_path = cmd_parser(sys.argv[1:])
	tester = TestManager(sim_dir_path, telem_csv_path)
	tester.run_offline_fault_ID()
	tester.export_results()
