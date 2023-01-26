import pandas as pd
import numpy as np
import collections
from typing import List, Dict



class Identifier:
	def __init__(self, name: str, dim: int):
		self.name = name
		self.dim = dim
		self.sim_data = {}
		self.innov_hist_dict = {}
		self.Q = np.zeros((self.dim, self.dim))
		self.R = 0.1 * np.identity(self.dim)
		self.Px = self.Q
		self.C = np.identity(self.dim)
		self.innov_uncertainty_dict = {}
		self.sphere_contains_zero = {}
		self.N = 6 # adaptive window size
		self.chi = -1
		if self.dim == 8:
			self.chi = 17.535
		elif self.dim == 4:
			self.chi = 11.143
		elif self.dim == 3:
			self.chi = 9.348
		elif self.dim == 2:
			self.chi = 7.378
		elif self.dim == 1:
			self.chi = 5.024
		assert self.chi > 0, "Chi-Squared value must be larger than 0."
		self.mode_dets = []
		
	def run_offline_fault_ID(self, truth_telem: pd.DataFrame) -> List[str]:
		"""
		This is the main fault ID function for "offline" operation.
		This function iterates through the truth telemetry data and 
		treats every row as a measurement. Every measurement corresponds to
		an identified mode. Note that the fault-specific methods are call
		via the sub-classes.
		Input: pandas.DataFrame of truth data
		Output: A complete list of strings representing the identified mode/fault at each time step
		"""
		print("%s: Running Fault ID algorithm." %self.name)
		for (idx, series) in truth_telem.iterrows():
			curr_time = series.loc['Time (ns)']
			curr_exp_meas_dict = self.get_expected_measurements(curr_time)
			curr_truth_meas = self.get_measurement(series)
			self.update_innovations(curr_exp_meas_dict, curr_truth_meas)
			self.update_innovation_uncertainty()
			self.update_chi_squared_spheres()
			self.determine_mode()
			# print(curr_time, self.mode_dets[-1])
			# print(self.sphere_contains_zero)
		print("%s: Fault ID complete." %self.name)
		return self.mode_dets

	def get_expected_measurements(self, time: np.float64) -> Dict[str, np.ndarray]:
		curr_meas = {}
		for mode, df in self.sim_data.items():
			curr_meas[mode] = self.sim_data[mode][time]
		return curr_meas

	def update_innovations(self, exp_meas_dict: Dict[str,np.ndarray], truth_meas: np.ndarray) -> None:
		# calculate the innovations and update list
		for mode, mode_meas in exp_meas_dict.items():
			mode_innov = np.subtract(truth_meas, mode_meas)
			if len(self.innov_hist_dict[mode]) < self.N:
				self.innov_hist_dict[mode].append(mode_innov)
			else:
				self.innov_hist_dict[mode].append(mode_innov)
				self.innov_hist_dict[mode].popleft()
		return None
	
	def update_innovation_uncertainty(self) -> None:
		for mode, mode_innov_deque in self.innov_hist_dict.items():
			curr_mode_innov = mode_innov_deque[-1]
			curr_mode_innov_uncertainty = self.C @ self.Px @ self.C.transpose() + self.R
			self.innov_uncertainty_dict[mode] = curr_mode_innov_uncertainty
		return None

	def update_chi_squared_spheres(self) -> None:
		for mode, mode_innov_deque in self.innov_hist_dict.items():
			# take the mean of mode_innov_deque
			mode_innov_mean = np.mean(mode_innov_deque, axis=0)
			# take the Mahalanobis distance assuming zero mean
			exp_mu = np.zeros((self.dim, 1))
			dist = np.sqrt((exp_mu - mode_innov_mean).transpose() @ np.linalg.inv(self.innov_uncertainty_dict[mode]) @ (exp_mu - mode_innov_mean))
			# determine if dist >= sqrt(chi^2 / N)
			if mode == "Nominal":
				dist = dist[0][0] / 0.9
			else:
				dist = dist[0][0] / 0.1
			if dist <= (np.sqrt(self.chi / self.N)):
				self.sphere_contains_zero[mode] = (True, dist)
			else:
				self.sphere_contains_zero[mode] = (False, dist)
		return None

	def return_2nd_element(self, tuple_1):
		return tuple_1[1][1]

	def determine_mode(self):
		# figure out the modes that contain zero
		possible_modes = [(k,v) for k, v in self.sphere_contains_zero.items() if v[0] is True]
		if len(possible_modes) == 1:
			self.mode_dets.append(possible_modes[0][0])
		elif len(possible_modes) == 0:
			self.mode_dets.append("Unknown Mode")
		elif ("Nominal", (True, 0.0)) in possible_modes:
			# this logic represents the situation where faults and nominal data are indistinguishable 
			self.mode_dets.append("Nominal")
		else:
			# return the minimum
			self.mode_dets.append(min(possible_modes, key=self.return_2nd_element)[0])

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Gets the fault-specific state from a row of telemetry data """
		pass

class CSS_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(CSS_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills an 8x1 numpy array with CSS measurement data """
		state_df = telemetry[[
							'CSS Cos Values  1 [-]', 'CSS Cos Values  2 [-]',
							'CSS Cos Values  3 [-]', 'CSS Cos Values  4 [-]', 
							'CSS Cos Values  5 [-]', 'CSS Cos Values  6 [-]', 
							'CSS Cos Values  7 [-]', 'CSS Cos Values  8 [-]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self.dim,1))
		return state

class RW_Encoder_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(RW_Encoder_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 4x1 numpy array with RW measurement data """
		state_df = telemetry[[
							'RW Omega  1 [rad/s]', 'RW Omega  2 [rad/s]',
							'RW Omega  3 [rad/s]', 'RW Omega  4 [rad/s]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self.dim,1))
		return state

class RW_Friction_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(RW_Friction_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 4x1 numpy array with RW measurement data """
		state_df = telemetry[[
							'RW Omega  1 [rad/s]', 'RW Omega  2 [rad/s]',
							'RW Omega  3 [rad/s]', 'RW Omega  4 [rad/s]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self.dim,1))
		return state

class Panel_Deployment_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Panel_Deployment_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 2x1 numpy array with Panel measurement data """
		state_df = telemetry[['Panel Angle [rad]', 'Panel Angle Rate [rad/s]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self.dim,1))
		return state

class Panel_Angle_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Panel_Angle_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 1x1 numpy array with Panel measurement data """
		# state_df = telemetry[['Panel Angle [rad]', 'Panel Angle Rate [rad/s]']]
		# state = state_df.to_numpy()
		state = np.array(telemetry['Panel Angle [rad]'])
		state = np.resize(state, (self.dim,1))
		return state

class Panel_Efficiency_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Panel_Efficiency_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 1x1 numpy array with Panel measurement data """
		# state_df = telemetry[['Panel Angle [rad]', 'Panel Angle Rate [rad/s]']]
		# state = state_df.to_numpy()
		state = np.array(telemetry['Supply Power [W]'])
		state = np.resize(state, (self.dim,1))
		return state

class Battery_Capacity_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Battery_Capacity_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 1x1 numpy array with Panel measurement data """
		# state_df = telemetry[['Panel Angle [rad]', 'Panel Angle Rate [rad/s]']]
		# state = state_df.to_numpy()
		state = np.array(telemetry['Stored Energy [Ws]'])
		state = np.resize(state, (self.dim,1))
		return state

class Power_Sink_Fault_Identifier(Identifier):
	"""
	This class is reponsible for providing all the css-fault specific 
	member functions.
	Specifically, 
		- get_measurement();
	"""
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Power_Sink_Fault_Identifier, self).__init__(name, dim)
		print("%s: Setting up. this may take a moment..." %self.name)
		for (key, df) in sim_data.items():
			self.sim_data[key] = {}
			self.innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self.get_measurement(row)
				self.sim_data[key][time] = state
		print("%s: Set-Up Complete." %self.name)

	def get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Fills a 1x1 numpy array with Panel measurement data """
		# state_df = telemetry[['Panel Angle [rad]', 'Panel Angle Rate [rad/s]']]
		# state = state_df.to_numpy()
		state = np.array(telemetry['Net Power [W]'])
		state = np.resize(state, (self.dim,1))
		return state

















