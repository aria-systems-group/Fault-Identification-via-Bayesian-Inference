"""
# ISC License (ISC)

# Copyright 2023 ARIA Systems Research, University of Colorado at Boulder

# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.

# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Author: Justin Kottinger
"""

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
			print("MBFID Help:")
			print("-----")
			print("Required Args:")
			print("--simulations,-s		The path to a simulation database (e.g. <path/to/simulations>)")
			print("--truth,-t			The path to the telemetry data. (e.g.  <path/to/truth>/telemetry.csv)")
			print("-----")
			print("Optional Args:")
			print("--help,-h			Explains how to run MBFID.")
			print("-----")
			print("Note: if --help or -h exists in the command line arguments, the MBFID tool will not run.")
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
