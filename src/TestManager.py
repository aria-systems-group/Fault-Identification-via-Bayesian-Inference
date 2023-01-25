import os
import pandas as pd
from typing import TypedDict
from src.Identifier import *


class ResultsType(TypedDict):
    CSS_ID: 		list[str]
    RW_ENCODER_ID: 	list[str]
    RW_FRICTION_ID: list[str]
    PANEL_DEPLOY_ID:list[str]
    PANEL_ANGLE_ID:	list[str]
    BATTERY_CAP_ID: list[str]
    POWER_SINK_ID:	list[str]

class TestManager:
	def __init__(self, simPath, telemPath, name="Test Manager"):
		self.path_to_sims = simPath
		self.path_to_telem = telemPath
		self.truth_telem_pd = None
		self.sim_telem_dict = {}
		self.__name = name
		self.__ready = self.run_sanity_checks()

	def run_sanity_checks(self):
		"""
		Pulls the data from path_to_sims and path_to_telem
		The path_to_sims is stored in a dictionary while the 
		path_to_telem data is saved to a pandas.Dataframe.
		input: NULL
		output: Boolean
		Data initialized: 
			- sim_telem_dict
			- truth_telem_pd
		"""
		# try to create the simulation telemetry dictionary
		try:
			sim_dirs = [x[0] for x in os.walk(self.path_to_sims)][1:]
			for name in sim_dirs:
				sim_mode = os.path.basename(name)
				sim_telem_path = name + "/telemetry.csv"
				sim_telem_df = pd.read_csv(sim_telem_path)
				sim_telem_df.rename( columns={'Unnamed: 0':'Time (ns)'}, inplace=True )
				self.sim_telem_dict[sim_mode] = sim_telem_df
				# print(sim_mode, sim_telem_path)
		except:
			print("Path Error!")
			print("The provided argument %s must point directly to an existing simulation database." % self.path_to_sim)
			print("If you designed the database yourself, be sure the database is properly set-up.")
			return False
		
		# try to create the truth telemetry DataFrame
		try:
			self.truth_telem_pd = pd.read_csv(self.path_to_telem)
			self.truth_telem_pd.rename( columns={'Unnamed: 0':'Time (ns)'}, inplace=True )
		except:
			print("Path Error!")
			print("The provided argument %s must point directly to an existing *.csv file." % self.path_to_telem)
			return False
		# exit(1)
		return True
		

	# the main fault id function
	def run_offline_fault_ID(self, testType="all") -> ResultsType:
		"""
		This is the main fault ID function. It creates the
		required test objects and tasks each one with fault ID.
		input: NULL
		output: ResultsType 
		Data initialized: 
			- sim_telem_dict
			- truth_telem_pd
		"""
		assert(self.__ready is True)

		results = ResultsType({'CSS':[], 'RW':[]})

		print("%s: Testing for %s faults on the telemetry data found at %s" 
				%(self.__name, testType, self.path_to_telem))

		if testType == "all":
			"""
			We will test all faults in the following order:
				1. CSS
				2. RW
			"""
			# # 1. create css fault tester by collecting its expected data
			# this will be optimized in future commits
			# css_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "CSSFAULT" in key:
			# 		css_data[key] = value
			# 	elif "None_None_None" in key:
			# 		css_data["Nominal"] = value
			# css_tester = CSS_Fault_Identifier("CSS Fault Tester", 8, css_data)
			# css_tester.run_offline_fault_ID(self.truth_telem_pd)
			# results['CSS'] = css_tester.mode_dets

			# # 2. create rw encoder fault tester by collecting its expected data
			# # this will be optimized in future commits
			# rw_encode_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "SIGNAL" in key:
			# 		rw_encode_data[key] = value
			# 	elif "None_None_None" in key:
			# 		rw_encode_data["Nominal"] = value
			# rw_encoder_tester = RW_Encoder_Fault_Identifier("RW Encoder Tester", 4, rw_encode_data)
			# rw_encoder_tester.run_offline_fault_ID(self.truth_telem_pd)

			# # 3. create rw friction fault tester by collecting its expected data
			# # this will be optimized in future commits
			# rw_friction_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "FRICTION" in key:
			# 		rw_friction_data[key] = value
			# 	elif "None_None_None" in key:
			# 		rw_friction_data["Nominal"] = value
			# rw_encoder_tester = RW_Friction_Fault_Identifier("RW Friction Tester", 4, rw_friction_data)
			# rw_encoder_tester.run_offline_fault_ID(self.truth_telem_pd)

			# # 4. create panel deployment fault tester by collecting its expected data
			# panel_deploy_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "DEPLOY" in key:
			# 		panel_deploy_data[key] = value
			# 	elif "None_None_None" in key:
			# 		panel_deploy_data["Nominal"] = value
			# panel_deployment_tester = Panel_Deployment_Fault_Identifier("Panel Deployment Tester", 2, panel_deploy_data)
			# panel_deployment_tester.run_offline_fault_ID(self.truth_telem_pd)

			# # 5. create panel angle fault tester by collecting its expected data
			# panel_angle_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "ANGLEFAULT" in key:
			# 		panel_angle_data[key] = value
			# 	elif "None_None_None" in key:
			# 		panel_angle_data["Nominal"] = value
			# panel_angle_tester = Panel_Angle_Fault_Identifier("Panel Angle Tester", 1, panel_angle_data)
			# panel_angle_tester.run_offline_fault_ID(self.truth_telem_pd)

			# # 6. create panel angle fault tester by collecting its expected data
			# panel_efficiency_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "EFFICIENCY" in key:
			# 		panel_efficiency_data[key] = value
			# 	elif "None_None_None" in key:
			# 		panel_efficiency_data["Nominal"] = value
			# panel_efficiency_tester = Panel_Efficiency_Fault_Identifier("Panel Efficiency Tester", 1, panel_efficiency_data)
			# panel_efficiency_tester.run_offline_fault_ID(self.truth_telem_pd)

			# # 7. create battery capacity fault tester by collecting its expected data
			# battery_capacity_data = {}
			# for key, value in self.sim_telem_dict.items():
			# 	if "BatteryCapacity" in key:
			# 		battery_capacity_data[key] = value
			# 	elif "None_None_None" in key:
			# 		battery_capacity_data["Nominal"] = value
			# battery_capacity_tester = Battery_Capacity_Fault_Identifier("Battery Capacity Tester", 1, battery_capacity_data)
			# battery_capacity_tester.run_offline_fault_ID(self.truth_telem_pd)

			# 8. create power sink fault tester by collecting its expected data
			power_sink_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PowerSink" in key:
					power_sink_data[key] = value
				elif "None_None_None" in key:
					power_sink_data["Nominal"] = value
			power_sink_tester = Power_Sink_Fault_Identifier("Power Sink Tester", 1, power_sink_data)
			power_sink_tester.run_offline_fault_ID(self.truth_telem_pd)

		return results











			

