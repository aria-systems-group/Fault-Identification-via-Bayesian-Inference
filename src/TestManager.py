import os
import pandas as pd
from src.FaultIdentifier import *


class TestManager:
	""" TestManager is the main MBFID class. As its name suggests, 
	it manages the data that is imported/exported through the main 
	Bayesian Hypothesis Testing class (see FaultIdentifier.py). 
	"""
	def __init__(self, sim_dir_path, telem_csv_path, name="Test Manager"):
		self.sim_dir_path = sim_dir_path
		self.telem_csv_path = telem_csv_path
		self.sim_telem_dict = {}
		self.truth_telem_df = {}
		self.__name = name
		self.__results_dict = {}
		self.__ready = self.__set_up()

	def __set_up(self) -> bool:
		""" Extracts the meaningful data hidden inside
		self.sim_dir_path and self.telem_csv_path. 
		"self.sim_telem_dict" becomes a Dict[str, pandas.DataFrame] 
		where str is the simulated mode name (e.g. "NominalSimulation") 
		and the pandas.DataFrame maintains the telemetry data for that mode.
		"self.truth_telem_df" becomes a pandas.DataFrame filled with
		the truth telemetry data.

		Note: BSK does not name the time column. This function names the column
		as a bookkeeping technique for Hypothesis Testing. 
		"""
		# fill self.sim_telem_dict
		try:
			mode_dir_paths = [x[0] for x in os.walk(self.sim_dir_path)][1:]
			for mode_dir_path in mode_dir_paths:
				mode = os.path.basename(mode_dir_path)
				mode_telem_path = mode_dir_path + "/telemetry.csv"
				mode_telem_df = pd.read_csv(mode_telem_path)
				mode_telem_df.rename( columns={'Unnamed: 0':'Time (ns)'}, inplace=True )
				self.sim_telem_dict[mode] = mode_telem_df
		except:
			print("%s: Path Error!", self.__name)
			print("%s: The provided argument %s must point directly to an existing simulation database." % (self.__name, self.path_to_sim))
			print("%s: If you designed the database yourself, be sure the database is properly set-up." % self.__name)
			return False
		
		# fill self.truth_telem_df
		try:
			self.truth_telem_df = pd.read_csv(self.telem_csv_path)
			self.truth_telem_df.rename( columns={'Unnamed: 0':'Time (ns)'}, inplace=True )
		except:
			print("%s: Path Error!" %self.__name)
			print("%s: The provided argument %s must point directly to an existing *.csv file." % (self.__name, self.telem_csv_path))
			return False
		return True
	
	def name_css_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		seperated_name = dir_name.split(".")
		fault_type = None
		value = None
		name = None
		sensorIdx = seperated_name[-1]
		if "MAX" in seperated_name[1]:
			fault_type = "Stuck at Max Value"
		elif "RAND" in seperated_name[1]:
			fault_type = "Providing Random Values"
		elif "OFF" in seperated_name[1]:
			fault_type = "Is Off"
		elif "STUCK" in seperated_name[1]:
			fault_type = "Stuck"
			value = seperated_name[2] + "." + seperated_name[3]

		if value is not None:
			name = "CSS[" + sensorIdx + "]" + " " + fault_type + " near " + value
		else:
			name = "CSS[" + sensorIdx + "]" + " " + fault_type
		return name

	def name_rw_encoder_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		seperated_name = dir_name.split(".")
		fault_type = None
		wheel = seperated_name[-1]
		if "OFF" in seperated_name[1]:
			fault_type = "Is Off"
		elif "STUCK" in seperated_name[1]:
			fault_type = "Is Stuck"
		name = "RW[" + wheel + "]" + " " + fault_type
		return name

	def name_rw_friction_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		seperated_name = dir_name.split(".")
		fault_type = "Friction increased by " + seperated_name[1]
		wheel = seperated_name[-1]
		name = "RW[" + wheel + "]" + " " + fault_type
		return name

	def name_panel_deployment_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		seperated_name = dir_name.split(".")
		value = seperated_name[-2] + "." + seperated_name[-1]
		name = "Panel Deployment Stuck near " + str(round((float(value)*100),1)) + "%"
		return name

	def name_panel_angle_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		seperated_name = dir_name.split(".")
		value = None
		if "negative" in seperated_name[1]:
			value = "-" + seperated_name[-2] + "." + seperated_name[-1]
		elif "0" in seperated_name[-1]:
			value = seperated_name[-1]
		else:
			value = seperated_name[-2] + "." + seperated_name[-1]
		name = "Panel Angle Stuck near " + value + " [rad]"
		return name

	def name_panel_efficiency_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		return "Panel Efficiency Decreased to 70%"

	def name_batt_cap_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		return "Battery Capacity Decreased"

	def name_power_sink_mode(self, dir_name: str) -> str:
		""" Takes a fault directory name and returns a nicely formatted fault name """
		seperated_name = dir_name.split(".")
		value = None
		value = seperated_name[-2] + "." + seperated_name[-1]
		name = "Power Sink is approximately " + str(round((float(value)*100),1)) + "\% of nominal"
		return name


	# the main fault id function
	def run_offline_fault_ID(self, test_type: str = "all") -> None:
		""" This is the main MBFID function. The test manager will
		run test_type by initializing a FaultIdentifier object
		for every desired mode. The FaultIdentifier will perform the
		test based on the data that TestManager provides. 
		After the test is complete, TestManager requests the resulting
		mode ID's from the FaultIdentifier and stores in self.__results_dict.
		At the end of this function, self.__results_dict is a 
		Dict[str, List[str]] where str is the test_type (e.g. "CSS_ID")
		and List[str] is a list of mode ID's that were generated during 
		the test. The ith element of the list cooresponds to the mode
		ID'd given the ith row of telemetry data. In other words, for 
		the measurement given at the time-step of row i.

		Keyword arguments:
		test_type: str -- the list of all command line arguments
		
		Note: Single-fault test_type's are not currently supported.
		"""
		assert(self.__ready is True)

		print("%s: Testing for %s faults on the telemetry data found at %s." 
			%(self.__name, test_type, self.telem_csv_path))

		if test_type == "all":
			"""
			Tests all faults in the following order:
				1. CSS
				2. RW Encoder
				3. RW Friction
				4. Panel Deployment
				5. Panel Angle 
				6. Panel Efficiency
				7. Battery Capacity
				8. Power Sink
			Note: Set-up for these Fault ID tests requires creating 
			a dictionary Dict[str, pandas.DataFrame] where str is 
			a nicely formatted fault name and the pandas.Dataframe 
			holds the telemetry data for that mode. The FaultIdentifier
			will take care of the rest and return a list of modes. 
			"""
			# 1. Run CSS Fault ID
			css_data = {}
			for key, value in self.sim_telem_dict.items():
				if "CssSignalFault" in key:
					fault_name = self.name_css_mode(key)
					css_data[fault_name] = value
				elif "Nominal" in key:
					css_data["Nominal"] = value
			css_tester = CSS_FaultIdentifier(name="CSS Fault Tester", 
											dim=8, 
											sim_data=css_data)
			css_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['CSS_ID'] = css_tester.mode_ids

			# 2. Run RW Encoder Fault ID
			rw_encode_data = {}
			for key, value in self.sim_telem_dict.items():
				if "RwEncoderFault" in key:
					fault_name = self.name_rw_encoder_mode(key)
					rw_encode_data[fault_name] = value
				elif "Nominal" in key:
					rw_encode_data["Nominal"] = value
			rw_encoder_tester = RW_Encoder_FaultIdentifier(name="RW Encoder Tester", 
															dim=4, 
															sim_data=rw_encode_data)
			rw_encoder_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['RW_ENCODER_ID'] = rw_encoder_tester.mode_ids

			# 3. Run RW Friction Fault ID
			rw_friction_data = {}
			for key, value in self.sim_telem_dict.items():
				if "RwFrictionFault" in key:
					fault_name = self.name_rw_friction_mode(key)
					rw_friction_data[fault_name] = value
				elif "Nominal" in key:
					rw_friction_data["Nominal"] = value
			rw_friction_tester = RW_Friction_FaultIdentifier(name="RW Friction Tester", 
															dim=4, 
															sim_data=rw_friction_data)
			rw_friction_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['RW_FRICTION_ID'] = rw_friction_tester.mode_ids

			# 4. Run Panel Deployment Fault ID
			panel_deploy_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PanelDeploymentFault" in key:
					fault_name = self.name_panel_deployment_mode(key)
					panel_deploy_data[fault_name] = value
				elif "Nominal" in key:
					panel_deploy_data["Nominal"] = value
			panel_deployment_tester = Panel_Deployment_FaultIdentifier(name="Panel Deployment Tester", 
																		dim=2, 
																		sim_data=panel_deploy_data)
			panel_deployment_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['PANEL_DEPLOY_ID'] = panel_deployment_tester.mode_ids

			# 5. Run Panel Angle Fault ID
			panel_angle_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PanelAngleFault" in key:
					fault_name = self.name_panel_angle_mode(key)
					panel_angle_data[fault_name] = value
				elif "Nominal" in key:
					panel_angle_data["Nominal"] = value
			panel_angle_tester = Panel_Angle_FaultIdentifier(name="Panel Angle Tester", 
															dim=1, 
															sim_data=panel_angle_data)
			panel_angle_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['PANEL_ANGLE_ID'] = panel_angle_tester.mode_ids

			# 6. Run Panel Efficiency Fault ID
			panel_efficiency_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PanelEfficiencyFault" in key:
					fault_name = self.name_panel_efficiency_mode(key)
					panel_efficiency_data[fault_name] = value
				elif "Nominal" in key:
					panel_efficiency_data["Nominal"] = value
			panel_efficiency_tester = Panel_Efficiency_FaultIdentifier(name="Panel Efficiency Tester", 
																		dim=1, 
																		sim_data=panel_efficiency_data)
			panel_efficiency_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['PANEL_EFF_ID'] = panel_efficiency_tester.mode_ids

			# 7. Run Battery Capacity Fault ID
			battery_capacity_data = {}
			for key, value in self.sim_telem_dict.items():
				if "BatteryCapacity" in key:
					fault_name = self.name_batt_cap_mode(key)
					battery_capacity_data[fault_name] = value
				elif "Nominal" in key:
					battery_capacity_data["Nominal"] = value
			battery_capacity_tester = Battery_Capacity_FaultIdentifier(name="Battery Capacity Tester", 
																		dim=1, 
																		sim_data=battery_capacity_data)
			battery_capacity_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['BATTERY_CAP_ID'] = battery_capacity_tester.mode_ids

			# 8. Run Power Sink Fault ID
			power_sink_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PowerSinkFault" in key:
					fault_name = self.name_power_sink_mode(key)
					power_sink_data[fault_name] = value
				elif "Nominal" in key:
					power_sink_data["Nominal"] = value
			power_sink_tester = Power_Sink_FaultIdentifier(name="Power Sink Tester", 
															dim=1, 
															sim_data=power_sink_data)
			power_sink_tester.run_offline_fault_ID(self.truth_telem_df)
			self.__results_dict['POWER_SINK_ID'] = power_sink_tester.mode_ids
		else:
			print("%s ERROR: running the tool with type %s is not yet implemented." %(self.__name, testType))
		return None

	def export_results(self) -> None:
		""" Exports the Fault ID test results inside
		self.__results_dict to a csv using the pandas.DataFrame 
		interface. The results are saved inside ./results
		and are named identically to the truth example ID. 
		"""
		results_dir = "results/"
		if not os.path.exists(results_dir):
			os.mkdir(results_dir)
		
		self.__results_dict["Time (ns)"] = self.truth_telem_df["Time (ns)"].tolist()
		results_df = pd.DataFrame.from_dict(self.__results_dict)
		results_df = results_df.set_index('Time (ns)')
		example_id = self.telem_csv_path.split("/")[-2]
		results_df.to_csv(results_dir + example_id + ".csv")
