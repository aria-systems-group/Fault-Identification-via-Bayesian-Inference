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
import numpy as np
import collections
from typing import List, Dict



class FaultIdentifier:
	""" This is an Abstract Class that runs the main 
	Bayesian Hypothesis Testing algorithm. Given
	truth data, it runs self.run_offline_fault_ID() 
	to fill self.mode_dets with the Fault ID results.
	To implement the class, one must implement self.get_measurement()
	"""
	def __init__(self, name: str, dim: int):
		self.mode_ids = []
		self._name = name
		self._dim = dim
		self._sim_data = {}
		self._innov_hist_dict = {}
		self.__Q = 0.0 * np.identity(self._dim)
		self.__R = 0.1 * np.identity(self._dim)
		self.__Px = self.__Q
		self.__C = np.identity(self._dim)
		self.__innov_uncertainty_dict = {}
		self.__sphere_contains_zero_dict = {}
		self.__N = 6
		# Chi-Squared constant for 95% confidence interval depends on system DoF
		self.__chi = -1  
		if self._dim == 8:
			self.__chi = 17.535
		elif self._dim == 4:
			self.__chi = 11.143
		elif self._dim == 3:
			self.__chi = 9.348
		elif self._dim == 2:
			self.__chi = 7.378
		elif self._dim == 1:
			self.__chi = 5.024
		assert self.__chi > 0, "Chi-Squared value must be larger than 0."

	def run_offline_fault_ID(self, truth_telem: pd.DataFrame) -> List[str]:
		""" This is the main fault ID function for "offline" operation.
		This function iterates through the truth telemetry data and 
		treats every row as a measurement. A single mode is identified for 
		every measurement and saved inside self.mode_ids. 
		
		Keyword arguments:
		truth_telem: pandas.DataFrame -- the truth telemetry data 

		Output: A list of strings representing the identified fault for every measurement
		"""
		print("%s: Running Fault ID algorithm." %self._name)
		for (idx, series) in truth_telem.iterrows():
			curr_time = series.loc['Time (ns)']
			curr_exp_meas_dict = self.__get_expected_measurements(curr_time)
			curr_truth_meas = self._get_measurement(series)
			self.__update_innovations(curr_exp_meas_dict, curr_truth_meas)
			self.__update_innovation_uncertainty()
			self.__update_chi_squared_spheres()
			self.__determine_mode()
			# Uncomment for debugging, as needed
			# print(curr_time, self.mode_ids[-1])
			# print(self.__sphere_contains_zero_dict)
			# input("enter to continue")
		# print("%s: Fault ID complete." %self._name)
		return self.mode_ids

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Gets the fault-specific measurement from a single-row of telemetry data 

		Keyword arguments:
		telemetry: pandas.Series -- the telemetry data for a specific time step

		Output: a (self._dim x 1) np.ndarray representing the measurement. 
		"""
		pass

	def __get_expected_measurements(self, time: float) -> Dict[str, np.ndarray]:
		""" This function extracts the expected measurement for every
		fault mode. 
		
		Keyword arguments:
		time: float -- the time stamp (in ns)

		Output: Dict[str, np.ndarray] -- a dictionary where str is the fault mode
		and the np.ndarray is the expected state for the corresponding time.
		"""
		curr_meas = {}
		for mode, df in self._sim_data.items():
			curr_meas[mode] = self._sim_data[mode][time]
		return curr_meas

	def __update_innovations(self, exp_meas_dict: Dict[str,np.ndarray], truth_meas: np.ndarray) -> None:
		""" This function updates self._innov_hist_dict which is represents a 
		moving window of the self.__N most recent innovations
		
		Keyword arguments:
		exp_meas_dict: Dict[str,np.ndarray] -- a dictionary where str is the fault mode
		and the np.ndarray is the expected state.
		truth_meas: np.ndarray -- the most recent truth measurement
		"""
		for mode, mode_meas in exp_meas_dict.items():
			mode_innov = np.subtract(truth_meas, mode_meas)
			if len(self._innov_hist_dict[mode]) < self.__N:
				self._innov_hist_dict[mode].append(mode_innov)
			else:
				self._innov_hist_dict[mode].append(mode_innov)
				self._innov_hist_dict[mode].popleft()
		return None
	
	def __update_innovation_uncertainty(self) -> None:
		""" This function the covariance of every fault mode's innovations. """
		for mode, mode_innov_deque in self._innov_hist_dict.items():
			curr_mode_innov = mode_innov_deque[-1]
			curr_mode_innov_uncertainty = self.__C @ self.__Px @ self.__C.transpose() + self.__R
			self.__innov_uncertainty_dict[mode] = curr_mode_innov_uncertainty
		return None

	def __update_chi_squared_spheres(self) -> None:
		""" Updates the 95% confidence ellipsoids given the updated data. It 
		also determines if the resulting ellipsoid contains the origin. The result 
		is used for fault ID. 
		"""
		for mode, mode_innov_deque in self._innov_hist_dict.items():
			mode_innov_mean = np.mean(mode_innov_deque, axis=0)
			# calc the Mahalanobis distance assuming zero mean
			exp_mu = np.zeros((self._dim, 1))
			s_inv = np.diag(1/self.__innov_uncertainty_dict[mode].diagonal())
			dist = np.sqrt((exp_mu - mode_innov_mean).transpose() @ s_inv @ (exp_mu - mode_innov_mean))[0][0]
			if dist <= (np.sqrt(self.__chi / self.__N)):
				self.__sphere_contains_zero_dict[mode] = (True, dist)
			else:
				self.__sphere_contains_zero_dict[mode] = (False, dist)
		return None

	def __return_2nd_element(self, nested_tuple) -> float:
		""" Extracts the 2nd element of the 2nd element of a nested tuple. 

		Keyword arguments:
		nested_tuple: Tuple[str, Tuple[bool, float]]
		"""
		return nested_tuple[1][1]

	def __determine_mode(self) -> None:
		""" Performs the required logic on self.__sphere_contains_zero_dict to correclty
		identify the fault mode.
		"""
		# extract the modes that contain zero
		possible_modes = [(k,v) for k, v in self.__sphere_contains_zero_dict.items() if v[0] is True]
		if len(possible_modes) == 1:
			self.mode_ids.append(possible_modes[0][0])
		elif len(possible_modes) == 0:
			self.mode_ids.append("Unknown Mode") # unknown anomaly
		elif len(self.mode_ids) >= 1:
			val = min(possible_modes, key=self.__return_2nd_element)[1][1]
			if (self.mode_ids[-1], (True, val)) in possible_modes:
				# this logic represents the situation where faults and nominal data are indistinguishable 
				self.mode_ids.append(self.mode_ids[-1])
			else:
				# multiple possible ID's -- return the one whose mean is closest to 0
				self.mode_ids.append(min(possible_modes, key=self.__return_2nd_element)[0])
		else:
			val = min(possible_modes, key=self.__return_2nd_element)[1][1]
			if ("Nominal", (True, val)) in possible_modes:
				# this logic represents the situation where faults and nominal data are indistinguishable 
				self.mode_ids.append("Nominal")
			else:
				# multiple possible ID's -- return the one whose mean is closest to 0
				self.mode_ids.append(min(possible_modes, key=self.__return_2nd_element)[0])
		return None

class CSS_FaultIdentifier(FaultIdentifier):
	""" The CSS Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(CSS_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns CSS measurement data as an 8x1 numpy array from full telemetry data. """
		state_df = telemetry[[
							'CSS Cos Values  1 [-]', 'CSS Cos Values  2 [-]',
							'CSS Cos Values  3 [-]', 'CSS Cos Values  4 [-]', 
							'CSS Cos Values  5 [-]', 'CSS Cos Values  6 [-]', 
							'CSS Cos Values  7 [-]', 'CSS Cos Values  8 [-]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self._dim, 1))
		return state

class RW_Encoder_FaultIdentifier(FaultIdentifier):
	""" The RW Encoder Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(RW_Encoder_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		# since RW range is so large, we need to dramatically increase the noise params
		self.R = 250 * np.identity(self._dim)
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns RW measurement data as an 4x1 numpy array from full telemetry data. """
		state_df = telemetry[[
							'RW Omega  1 [rad/s]', 'RW Omega  2 [rad/s]',
							'RW Omega  3 [rad/s]', 'RW Omega  4 [rad/s]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self._dim, 1))
		return state

class RW_Friction_FaultIdentifier(FaultIdentifier):
	""" The RW Friction Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(RW_Friction_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		# this fault is VERY subtle
		self.R = 1E-20 * np.identity(self._dim)
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns RW measurement data as an 4x1 numpy array from full telemetry data. """
		# state_df = telemetry[[
		# 					'RW Omega  1 [rad/s]', 'RW Omega  2 [rad/s]',
		# 					'RW Omega  3 [rad/s]', 'RW Omega  4 [rad/s]']]
		state_df = telemetry[[
							'RW Torque  1 [Nm]', 'RW Torque  2 [Nm]',
							'RW Torque  3 [Nm]', 'RW Torque  4 [Nm]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self._dim, 1))
		return state

class Panel_Deployment_FaultIdentifier(FaultIdentifier):
	""" The Panel Deployment Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Panel_Deployment_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns Panel Angle measurement data as an 2x1 numpy array from full telemetry data. """
		state_df = telemetry[['Panel Angle [rad]', 'Panel Angle Rate [rad/s]']]
		state = state_df.to_numpy()
		state = np.resize(state, (self._dim, 1))
		return state

class Panel_Angle_FaultIdentifier(FaultIdentifier):
	""" The Panel Angle Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Panel_Angle_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns Panel Angle measurement data as an 1x1 numpy array from full telemetry data. """
		state = np.array(telemetry['Panel Angle [rad]'])
		state = np.resize(state, (self._dim, 1))
		return state

class Panel_Efficiency_FaultIdentifier(FaultIdentifier):
	""" The Panel Efficiency Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Panel_Efficiency_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		self.R = 1E-10 * np.identity(self._dim)
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns Supply Power measurement data as an 1x1 numpy array from full telemetry data. """
		state = np.array(telemetry['Supply Power [W]'])
		state = np.resize(state, (self._dim, 1))
		return state

class Battery_Capacity_FaultIdentifier(FaultIdentifier):
	""" The Battery Capacity Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Battery_Capacity_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.Series) -> np.ndarray:
		""" Returns Stored Energy measurement data as an 1x1 numpy array from full telemetry data. """
		state = np.array(telemetry['Stored Energy [Ws]'])
		state = np.resize(state, (self._dim, 1))
		return state

class Power_Sink_FaultIdentifier(FaultIdentifier):
	""" The Power Sink Fault specific implementation of the FaultIdentifier class """
	def __init__(self, name: str, dim: int, sim_data: Dict[str,pd.DataFrame]):
		super(Power_Sink_FaultIdentifier, self).__init__(name, dim)
		print("%s: Setting up... This may take a moment..." %self._name)
		for (key, df) in sim_data.items():
			self._sim_data[key] = {}
			self._innov_hist_dict[key] = collections.deque([])
			for index, row in df.iterrows():
				time = row['Time (ns)']
				state = self._get_measurement(row)
				self._sim_data[key][time] = state
		print("%s: Set-Up Complete." %self._name)

	def _get_measurement(self, telemetry: pd.DataFrame) -> np.ndarray:
		""" Returns Power Sink measurement data as an 1x1 numpy array from full telemetry data. """
		state = np.array(telemetry['Net Power [W]'])
		state = np.resize(state, (self._dim, 1))
		return state
