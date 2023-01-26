import os
import pandas as pd
from src.Identifier import *


class TestManager:
	def __init__(self, simPath, telemPath, name="Test Manager"):
		self.path_to_sims = simPath
		self.path_to_telem = telemPath
		self.truth_telem_pd = None
		self.sim_telem_dict = {}
		self.__name = name
		self.__ready = self.run_sanity_checks()
		self.__results = {}

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
	
	def name_css_mode(self, dir_name: str) -> str:
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
		seperated_name = dir_name.split(".")
		fault_type = "Friction increased by " + seperated_name[1]
		wheel = seperated_name[-1]
		name = "RW[" + wheel + "]" + " " + fault_type
		return name

	def name_panel_deployment_mode(self, dir_name: str) -> str:
		seperated_name = dir_name.split(".")
		value = seperated_name[-2] + "." + seperated_name[-1]
		name = "Panel Deployment Stuck near " + value + "%"
		return name

	def name_panel_angle_mode(self, dir_name: str) -> str:
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
		return "Panel Efficiency Decreased to 70%"

	def name_batt_cap_mode(self, dir_name: str) -> str:
		return "Battery Capacity Decreased"

	def name_power_sink_mode(self, dir_name: str) -> str:
		seperated_name = dir_name.split(".")
		value = None
		if "negative" in seperated_name[1]:
			value = "-" + seperated_name[-2] + "." + seperated_name[-1]
		else:
			value = seperated_name[-2] + "." + seperated_name[-1]
		name = "Panel Angle Stuck near " + value + " [rad]"
		return name


	# the main fault id function
	def run_offline_fault_ID(self, testType="all") -> None:
		"""
		This is the main fault ID function. It creates the
		required test objects and tasks each one with fault ID.
		input: NULL
		output: None 
		Data initialized: 
			- sim_telem_dict
			- truth_telem_pd
		"""
		assert(self.__ready is True)

		print("%s: Testing for %s faults on the telemetry data found at %s" 
				%(self.__name, testType, self.path_to_telem))

		if testType == "all":
			"""
			Will test all faults in the following order:
				1. CSS
				2. RW Encoder
				3. RW Friction
				4. Panel Deployment
				5. Panel Angle 
				6. Panel Efficiency
				7. Battery Capacity
				8. Power Sink
			"""
			# 1. create css fault tester by collecting its expected data
			css_data = {}
			for key, value in self.sim_telem_dict.items():
				if "CssSignalFault" in key:
					fault_name = self.name_css_mode(key)
					css_data[fault_name] = value
				elif "Nominal" in key:
					css_data["Nominal"] = value
			css_tester = CSS_Fault_Identifier("CSS Fault Tester", 8, css_data)
			css_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['CSS_ID'] = css_tester.mode_dets

			# 2. create rw encoder fault tester by collecting its expected data
			rw_encode_data = {}
			for key, value in self.sim_telem_dict.items():
				if "RwEncoderFault" in key:
					fault_name = self.name_rw_encoder_mode(key)
					rw_encode_data[fault_name] = value
				elif "Nominal" in key:
					rw_encode_data["Nominal"] = value
			rw_encoder_tester = RW_Encoder_Fault_Identifier("RW Encoder Tester", 4, rw_encode_data)
			rw_encoder_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['RW_ENCODER_ID'] = rw_encoder_tester.mode_dets

			# 3. create rw friction fault tester by collecting its expected data
			rw_friction_data = {}
			for key, value in self.sim_telem_dict.items():
				if "RwFrictionFault" in key:
					fault_name = self.name_rw_friction_mode(key)
					rw_friction_data[fault_name] = value
				elif "Nominal" in key:
					rw_friction_data["Nominal"] = value
			rw_friction_tester = RW_Friction_Fault_Identifier("RW Friction Tester", 4, rw_friction_data)
			rw_friction_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['RW_FRICTION_ID'] = rw_friction_tester.mode_dets

			# 4. create panel deployment fault tester by collecting its expected data
			panel_deploy_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PanelDeploymentFault" in key:
					fault_name = self.name_panel_deployment_mode(key)
					panel_deploy_data[fault_name] = value
				elif "Nominal" in key:
					panel_deploy_data["Nominal"] = value
			panel_deployment_tester = Panel_Deployment_Fault_Identifier("Panel Deployment Tester", 2, panel_deploy_data)
			panel_deployment_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['PANEL_DEPLOY_ID'] = panel_deployment_tester.mode_dets

			# 5. create panel angle fault tester by collecting its expected data
			panel_angle_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PanelAngleFault" in key:
					fault_name = self.name_panel_angle_mode(key)
					panel_angle_data[fault_name] = value
				elif "Nominal" in key:
					panel_angle_data["Nominal"] = value
			panel_angle_tester = Panel_Angle_Fault_Identifier("Panel Angle Tester", 1, panel_angle_data)
			panel_angle_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['PANEL_ANGLE_ID'] = panel_angle_tester.mode_dets

			# 6. create panel efficiency fault tester by collecting its expected data
			panel_efficiency_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PanelEfficiencyFault" in key:
					fault_name = self.name_panel_efficiency_mode(key)
					panel_efficiency_data[fault_name] = value
				elif "Nominal" in key:
					panel_efficiency_data["Nominal"] = value
			panel_efficiency_tester = Panel_Efficiency_Fault_Identifier("Panel Efficiency Tester", 1, panel_efficiency_data)
			panel_efficiency_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['PANEL_EFF_ID'] = panel_efficiency_tester.mode_dets

			# 7. create battery capacity fault tester by collecting its expected data
			battery_capacity_data = {}
			for key, value in self.sim_telem_dict.items():
				if "BatteryCapacity" in key:
					fault_name = self.name_batt_cap_mode(key)
					battery_capacity_data[fault_name] = value
				elif "Nominal" in key:
					battery_capacity_data["Nominal"] = value
			battery_capacity_tester = Battery_Capacity_Fault_Identifier("Battery Capacity Tester", 1, battery_capacity_data)
			battery_capacity_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['BATTERY_CAP_ID'] = battery_capacity_tester.mode_dets

			# 8. create power sink fault tester by collecting its expected data
			power_sink_data = {}
			for key, value in self.sim_telem_dict.items():
				if "PowerSinkFault" in key:
					fault_name = self.name_power_sink_mode(key)
					power_sink_data[fault_name] = value
				elif "Nominal" in key:
					power_sink_data["Nominal"] = value
			power_sink_tester = Power_Sink_Fault_Identifier("Power Sink Tester", 1, power_sink_data)
			power_sink_tester.run_offline_fault_ID(self.truth_telem_pd)
			self.__results['POWER_SINK_ID'] = power_sink_tester.mode_dets
		else:
			print("ERROR: running the tool with type %s is not yet implemented." %testType)
		return None

	# save the results to text files
	def export_results(self) -> None:
		if not os.path.exists('Results/'):
			os.mkdir('results/')
		
		self.__results["Time (ns)"] = self.truth_telem_pd["Time (ns)"].tolist()
		results_df = pd.DataFrame.from_dict(self.__results)
		results_df = results_df.set_index('Time (ns)')

		example_id = self.path_to_telem.split("/")[-2]
		results_df.to_csv("results/" + example_id + ".csv")
		











