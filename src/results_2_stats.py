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

import pandas as pd
import os, sys
import re
from collections import Counter


def generate_detection_stats(modes_df, fault_time_s, fault, faulty_sensors, results_dict):
	fault_time_ns = fault_time_s * 1E9

	# initialize the statistics
	tp = 0
	tn = 0
	fp = 0
	fn = 0
	latency = 0
	latency_final = 0

	unknown_mode = "N/A"
	detected_list = []

	# see https://en.wikipedia.org/wiki/Sensitivity_and_specificity for details
	n = 0
	p = 0

	for time, detected_mode in modes_df.items():
		if time < fault_time_ns:
			n += 1
			# no fault occured yet
			if detected_mode == "Nominal":
				# detected no fault on negative sample
				# this is a true negative
				tn += 1
			else:
				# we detected a fault on negative sample
				# this is a false postive
				fp += 1
		else:
			p += 1
			# fault detected
			# correct_modes = [fault + str(s) for idx, s in enumerate(faulty_sensors) ]
			if (detected_mode != "Nominal"):
				# a correctly detected fault
				tp += 1
				latency_final = latency
			else:
				# a missed fault (so far)
				fn += 1
				latency += 1
			detected_list.append(detected_mode)
	

	# get most common mess up
	detected_mode_common = "Nominal"
	if len(detected_list) > 0:
		counter = Counter(detected_list)
		detected_mode_common = counter.most_common(1)[0][0]

	# see https://en.wikipedia.org/wiki/Sensitivity_and_specificity for details
	results_dict["FNR"] = fn / p
	results_dict["TPR"] = tp / p
	results_dict["FPR"] = fp / n
	results_dict["TNR"] = tn / n
	results_dict["Latency"] = latency_final
	results_dict["Detected_Fault"] = detected_mode_common
	if faulty_sensors == "None":
		results_dict["True_Fault"] = fault
	else:
		results_dict["True_Fault"] = fault + str(faulty_sensors[0])
	
	return results_dict

def generate_identification_stats(modes_df, fault_time_s, fault, faulty_sensors, results_dict):
	fault_time_ns = fault_time_s * 1E9

	# initialize the statistics
	tp = 0
	tn = 0
	fp = 0
	fn = 0
	latency = 0
	latency_final = 0

	unknown_mode = "N/A"
	id_list = []

	# see https://en.wikipedia.org/wiki/Sensitivity_and_specificity for details
	n = 0
	p = 0
	# this is a hacky variable. Used to find end of meaningful data inside PanelDeploymentFaults
	last_time = -1
	for time, id_mode in modes_df.items():
		if time < fault_time_ns:
			n += 1
			# no fault occured yet
			if "Nominal" in id_mode:
				# detected no fault on negative sample
				# this is a true negative
				tn += 1
			else:
				# we detected a fault on negative sample
				# this is a false postive
				fp += 1
		else:
			# print(fault)
			p += 1
			# fault id'd
			# correct_modes = [fault + str(s) for idx, s in enumerate(faulty_sensors) ]
			if "CSSFAULT_STUCK_MAX" in fault:
				if "Stuck" in id_mode and "Max" in id_mode and str(faulty_sensors) in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "CSSFAULT_OFF" in fault:
				if "Off" in id_mode and str(faulty_sensors) in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "CSSFAULT_STUCK_CURRENT" in fault or "CSSFAULT_STUCK_RAND" in fault:
				if "Stuck" in id_mode and str(faulty_sensors) in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "CSSFAULT_RAND" in fault:
				if "CSS" in id_mode and "Random" in id_mode and str(faulty_sensors) in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "SIGNAL_STUCK" in fault:
				if "Stuck" in id_mode and str(faulty_sensors) in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "SIGNAL_OFF" in fault:
				if "Off" in id_mode and str(faulty_sensors) in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "FRICTION_10x" in fault:
				if "Friction" in id_mode and "10x" in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "PanelAngleFault" in fault:
				if "Panel" in id_mode and "Stuck" in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "PanelDeploymentFault" in fault:
				if last_time > time:
					break
				if "Panel" in id_mode and "Deployment" in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
				last_time = time
			elif "PanelEfficiencyFault" in fault:
				if "Panel" in id_mode and "Efficiency" in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "BatteryCapacityFault" in fault:
				if "Battery" in id_mode and "Decreased" in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			elif "PowerSinkFault" in fault:
				if "Power Sink" in id_mode:
					# a correctly id'd fault
					tp += 1
					latency_final = latency
				else:
					# a missed fault (so far)
					fn += 1
					latency += 1
			else:
				print("ERROR in generate_identification_stats(): %s not implemented." %fault)
				exit(1)
			id_list.append(id_mode)
	

	# get most common mess up
	id_mode_common = "Nominal"
	if len(id_list) > 0:
		counter = Counter(id_list)
		id_list_common = counter.most_common(1)[0][0]

	# see https://en.wikipedia.org/wiki/Sensitivity_and_specificity for details
	results_dict["FNR"] = fn / p
	results_dict["TPR"] = tp / p
	results_dict["FPR"] = fp / n
	results_dict["TNR"] = tn / n
	results_dict["Latency"] = latency_final
	results_dict["Identified_Fault"] = id_list_common
	if faulty_sensors == "None":
		results_dict["True_Fault"] = fault
	else:
		results_dict["True_Fault"] = fault + str(faulty_sensors[0])
	
	return results_dict

def calc_css_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])

	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}
	if fault_data.empty:
		return rates_dict
	elif 'cssSignal' in fault_data['name'].values:
		
		msg = fault_data.loc[fault_data['name'] == 'cssSignal'].at[0,'message']
		time = fault_data.loc[fault_data['name'] == 'cssSignal'].at[0,'time [s]']
		fault = None
		if msg.find('CSSFAULT_STUCK_MAX') > -1:
			fault = 'CSSFAULT_STUCK_MAX_sensor_'
		elif msg.find('CSSFAULT_STUCK_RAND') > -1:
			fault = 'CSSFAULT_STUCK_RAND_sensor_'
		elif msg.find('CSSFAULT_STUCK_CURRENT') > -1:
			fault = 'CSSFAULT_STUCK_CURRENT_sensor_'
		elif msg.find('CSSFAULT_OFF') > -1:
			fault = 'CSSFAULT_OFF_sensor_'
		elif msg.find('CSSFAULT_RAND') > -1:
			fault = 'CSSFAULT_RAND'
		else:
			print(msg)
			print("FAULT NOT YET IMPLEMENTED")
		# need to figure out which sensor(s) failed
		faulty_sensors_str = re.findall(r'\[.*?\]', msg)[0]
		faulty_sensors_lst = eval(re.sub("\s+", ",", faulty_sensors_str.strip()))

		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['CSS_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['CSS_ID'], time, fault, faulty_sensors_lst, id_stats_dict)

	return det_stats_dict, id_stats_dict

def calc_RwEncode_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}
	
	if fault_data.empty:
		return rates_dict
	elif 'RwEncoder' in fault_data['name'].values:
		msg = fault_data.loc[fault_data['name'] == 'RwEncoder'].at[0,'message']
		time = fault_data.loc[fault_data['name'] == 'RwEncoder'].at[0,'time [s]']
		fault = None
		if msg.find('SIGNAL_STUCK') > -1:
			fault = 'SIGNAL_STUCK_wheel_'
		elif msg.find('SIGNAL_OFF') > -1:
			fault = 'SIGNAL_OFF_wheel_'
		# need to figure out which sensor(s) failed
		faulty_sensors_lst = []
		if msg.find('RW1') > -1:
			faulty_sensors_lst = [1]
		elif msg.find('RW2') > -1:
			faulty_sensors_lst = [2]
		elif msg.find('RW3') > -1:
			faulty_sensors_lst = [3]
		elif msg.find('RW4') > -1:
			faulty_sensors_lst = [4]

		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['RW_ENCODER_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['RW_ENCODER_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict, id_stats_dict

def calc_RwFric_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}

	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}
	if fault_data.empty:
		return rates_dict
	elif 'RwFriction' in fault_data['name'].values:
		msg = fault_data.loc[fault_data['name'] == 'RwFriction'].at[0,'message']
		time = fault_data.loc[fault_data['name'] == 'RwFriction'].at[0,'time [s]']
		fault = None
		if msg.find('5x') > -1:
			fault = 'FRICTION_5x'
		elif msg.find('10x') > -1:
			fault = 'FRICTION_10x'
		else:
			print(msg)
			print("FAULT NOT YET IMPLEMENTED")
		# need to figure out which sensor(s) failed
		faulty_sensors_lst = []
		if msg.find('RW1') > -1:
			faulty_sensors_lst = [1]
		elif msg.find('RW2') > -1:
			faulty_sensors_lst = [2]
		elif msg.find('RW3') > -1:
			faulty_sensors_lst = [3]
		elif msg.find('RW4') > -1:
			faulty_sensors_lst = [4]

		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['RW_FRICTION_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['RW_FRICTION_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict, id_stats_dict

def calc_panelDeployment_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}

	if fault_data.empty:
		return rates_dict
	elif 'deployment' in fault_data['name'].values:
		fault = "PanelDeploymentFault"
		'''
		time should actually be the time (in seconds) when 
		the truth hits the degrees listed in fault msg
		'''
		truth_telem = pd.read_csv(path2truth + "/telemetry.csv", index_col=[0])
		time = None
		last = 0
		for t, val in truth_telem['Panel Angle [rad]'].items():
			if (abs(val - last) < 0.001) and t > 305000000000:
				time = t * 1E-9
				break
			last = val
		
		assert(time is not None)

		# calculate statistics
		faulty_sensors_lst = "None"
		det_stats_dict = generate_detection_stats(test_data['PANEL_DEPLOY_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['PANEL_DEPLOY_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict, id_stats_dict

def calc_panelEfficiency_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}

	if fault_data.empty:
		return rates_dict
	elif 'panelEfficiency' in fault_data['name'].values:
		fault = "PanelEfficiencyFault"
		'''
		time should actually be the time (in seconds) when 
		the truth hits the degrees listed in fault msg
		'''
		time = fault_data.loc[fault_data['name'] == 'panelEfficiency'].at[0,'time [s]']

		# calculate statistics
		faulty_sensors_lst = "None"
		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['PANEL_EFF_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['PANEL_EFF_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict, id_stats_dict

def calc_BattCap_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}

	if fault_data.empty:
		return rates_dict
	elif 'batteryCapacity' in fault_data['name'].values:
		fault = "BatteryCapacityFault"
		'''
		time should actually be the time (in seconds) when 
		the truth hits the degrees listed in fault msg
		'''
		time = fault_data.loc[fault_data['name'] == 'batteryCapacity'].at[0,'time [s]']

		# calculate statistics
		faulty_sensors_lst = "None"
		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['BATTERY_CAP_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['BATTERY_CAP_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict, id_stats_dict

def calc_powerSink_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}

	if fault_data.empty:
		return rates_dict
	elif 'powerSink' in fault_data['name'].values:
		fault = "PowerSinkFault"
		'''
		time should actually be the time (in seconds) when 
		the truth hits the degrees listed in fault msg
		'''
		time = fault_data.loc[fault_data['name'] == 'powerSink'].at[0,'time [s]']
		faulty_sensors_lst = "None"
		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['POWER_SINK_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['POWER_SINK_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict,id_stats_dict

def calc_panelAngle_data(path2truth):
	example_id = os.path.basename(path2truth)
	fault_data = pd.read_csv(path2truth + "/faults.csv", index_col=[0])
	test_data = pd.read_csv("Results/" + example_id + ".csv", index_col=[0], keep_default_na=False, na_values=['_'])
	
	det_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Detected_Fault": "N/A",
						"True_Fault": "N/A"}
	id_stats_dict = {"Example_ID":example_id + "/",
						"TPR": "N/A",
						"FPR": "N/A",
						"TNR": "N/A",
						"FNR": "N/A",
						"Latency": "N/A",
						"Identified_Fault": "N/A",
						"True_Fault": "N/A"}

	if fault_data.empty:
		return rates_dict
	elif 'panelAng' in fault_data['name'].values:
		fault = "PanelAngleFault"
		'''
		time should actually be the time (in seconds) when 
		the truth hits the degrees listed in fault msg
		'''
		time = fault_data.loc[fault_data['name'] == 'panelAng'].at[0,'time [s]']

		# calculate statistics
		faulty_sensors_lst = "None"
		# calculate statistics
		det_stats_dict = generate_detection_stats(test_data['PANEL_ANGLE_ID'], time, fault, faulty_sensors_lst, det_stats_dict)
		id_stats_dict = generate_identification_stats(test_data['PANEL_ANGLE_ID'], time, fault, faulty_sensors_lst, id_stats_dict)
	return det_stats_dict, id_stats_dict


if __name__ == "__main__":
	'''
	This script turns all csv files from hyp_test.py into meaningful results like:
		TPR := Probability of fault occuring and being detected (good)
		FPR := Probability of fault occuring but not being detected (bad)
		TNR := Probability of no fault occuring and no fault detected (good)
		FNR := Probability of no fault occuring but dectecting a fault (bad)
		Latency := Time of fault occurance - Time of fault detection (successful detections only)
	'''

	# pull all results
	relativePath2Truth = "examples/Telemetry/"
	filenames = next(os.walk("results/"))[2]  # [] if no file
	if ".DS_Store" in filenames:
		filenames.remove(".DS_Store")

	# create CssFault results DF
	css_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])

	# create CssFault results DF
	css_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])
	# create RwEncode results DF
	RwEncode_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])
	# create RwEncode results DF
	RwEncode_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])
	# create RwFric results DF
	RwFric_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])
	# create RwFric results DF
	RwFric_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])
	# create Panel Deployment Fault results DF
	PanelDeployment_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])
	PanelDeployment_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])

	# create Panel Deployment Fault results DF
	PanelEff_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])
	PanelEff_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])

	# create Panel Deployment Fault results DF
	BattCap_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])
	BattCap_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])

	# create Panel Deployment Fault results DF
	PowerSink_det_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Detected_Fault", "True_Fault"])
	PowerSink_id_stats_total = pd.DataFrame(columns=["Example_ID", 
												"TPR_(1/100)", "FPR_(1/100)", 
												"TNR_(1/100)", "FNR_(1/100)",
												"Latency (k)", "Identified_Fault", "True_Fault"])
	
	# create Panel Angle Fault results DF
	PanelAngle_det_stats_total = pd.DataFrame(columns=["Example_ID", 
														"TPR_(1/100)", "FPR_(1/100)", 
														"TNR_(1/100)", "FNR_(1/100)",
														"Latency (k)", "Detected_Fault", "True_Fault"])
	PanelAngle_id_stats_total = pd.DataFrame(columns=["Example_ID", 
														"TPR_(1/100)", "FPR_(1/100)", 
														"TNR_(1/100)", "FNR_(1/100)",
														"Latency (k)", "Identified_Fault", "True_Fault"])
	
	# '''
	# To Do:
	# - Panel Efficiency Fault
	# - Battery Capacity Fault
	# '''
	for idx, file in enumerate(filenames):
		truthPath = relativePath2Truth + file[:-4]
		print(truthPath)
		# calc css stats for this example
		css_det_stats_example, css_id_stats_example = calc_css_data(truthPath)
		css_det_stats_total.loc[len(css_det_stats_total.index)] = list(css_det_stats_example.values()) 
		css_id_stats_total.loc[len(css_id_stats_total.index)] = list(css_id_stats_example.values()) 
	
		# calc RwEncode stats for this example
		rwencode_det_stats_example, rwencode_id_stats_example = calc_RwEncode_data(truthPath)
		RwEncode_det_stats_total.loc[len(RwEncode_det_stats_total.index)] = list(rwencode_det_stats_example.values()) 
		RwEncode_id_stats_total.loc[len(RwEncode_id_stats_total.index)] = list(rwencode_id_stats_example.values()) 
		
		# calc RwFric stats for this example
		RwFric_det_stats_example, RwFric_id_stats_example = calc_RwFric_data(truthPath)
		RwFric_det_stats_total.loc[len(RwFric_det_stats_total.index)] = list(RwFric_det_stats_example.values())
		RwFric_id_stats_total.loc[len(RwFric_id_stats_total.index)] = list(RwFric_id_stats_example.values())

		# calc Panel Deployment stats for this example
		PanelDeployment_det_stats_example, PanelDeployment_id_stats_example = calc_panelDeployment_data(truthPath)
		PanelDeployment_det_stats_total.loc[len(PanelDeployment_det_stats_total.index)] = list(PanelDeployment_det_stats_example.values()) 
		PanelDeployment_id_stats_total.loc[len(PanelDeployment_id_stats_total.index)] = list(PanelDeployment_id_stats_example.values())

		# calc Panel Efficiency stats for this example
		PanelEff_det_stats_example, PanelEff_id_stats_example = calc_panelEfficiency_data(truthPath)
		PanelEff_det_stats_total.loc[len(PanelEff_det_stats_total.index)] = list(PanelEff_det_stats_example.values()) 
		PanelEff_id_stats_total.loc[len(PanelEff_id_stats_total.index)] = list(PanelEff_id_stats_example.values())

		# calc Panel Efficiency stats for this example
		BattCap_det_stats_example, BattCap_id_stats_example = calc_BattCap_data(truthPath)
		BattCap_det_stats_total.loc[len(BattCap_det_stats_total.index)] = list(BattCap_det_stats_example.values()) 
		BattCap_id_stats_total.loc[len(BattCap_id_stats_total.index)] = list(BattCap_id_stats_example.values())

		# calc Power Sink Stats for this example
		PowerSink_det_stats_example, PowerSink_id_stats_example = calc_powerSink_data(truthPath)
		PowerSink_det_stats_total.loc[len(PowerSink_det_stats_total.index)] = list(PowerSink_det_stats_example.values()) 
		PowerSink_id_stats_total.loc[len(PowerSink_id_stats_total.index)] = list(PowerSink_id_stats_example.values())

		# calc Panel Angle Stats for this example
		PanelAngle_det_stats_example, PanelAngle_id_stats_example = calc_panelAngle_data(truthPath)
		PanelAngle_det_stats_total.loc[len(PanelAngle_det_stats_total.index)] = list(PanelAngle_det_stats_example.values()) 
		PanelAngle_id_stats_total.loc[len(PanelAngle_id_stats_total.index)] = list(PanelAngle_id_stats_example.values()) 

	
	isExist = os.path.exists("stats/")
	if not isExist:
		# Create a new directory because it does not exist
		os.mkdir("stats/")

	# export the results
	css_det_stats_total.to_csv("stats/CSS_det_stats.csv")
	css_id_stats_total.to_csv("stats/CSS_id_stats.csv")
	
	RwEncode_det_stats_total.to_csv("stats/RwEncode_det_stats.csv")
	RwEncode_id_stats_total.to_csv("stats/RwEncode_id_stats.csv")
	
	RwFric_det_stats_total.to_csv("stats/RwFriction_det_stats.csv")
	RwFric_id_stats_total.to_csv("stats/RwFriction_id_stats.csv")
	
	PanelDeployment_det_stats_total.to_csv("stats/PanelDeploy_det_stats.csv")
	PanelDeployment_id_stats_total.to_csv("stats/PanelDeploy_id_stats.csv")

	PanelEff_det_stats_total.to_csv("stats/PanelEfficiency_det_stats.csv")
	PanelEff_id_stats_total.to_csv("stats/PanelEfficiency_id_stats.csv")

	BattCap_det_stats_total.to_csv("stats/BattCap_det_stats.csv")
	BattCap_id_stats_total.to_csv("stats/BattCap_id_stats.csv")
	
	PowerSink_det_stats_total.to_csv("stats/PowerSink_det_stats.csv")
	PowerSink_id_stats_total.to_csv("stats/PowerSink_id_stats.csv")
	
	PanelAngle_det_stats_total.to_csv("stats/PanelAngle_det_stats.csv")
	PanelAngle_id_stats_total.to_csv("stats/PanelAngle_id_stats.csv")
