'''
Global performance metrics
'''
import pandas as pd
from timeit import default_timer 
import numpy as np
import pdb

from ephys2.lib.mpi import MPI
from .logger import logger

class Timer:
	def __init__(self):
		self.started = dict()
		self.accrued = dict()
		self.rank = MPI.COMM_WORLD.Get_rank()

	def start(self):
		if self.rank == 0:
			self.overall_start = default_timer()

	def start_step(self, name):
		if self.rank == 0:
			self.started[name] = default_timer()

	def stop_step(self, name) -> float:
		if self.rank == 0:
			delta = default_timer() - self.started[name]
			if name in self.accrued:
				self.accrued[name] += delta
			else:
				self.accrued[name] = delta
			return delta
		return 0

	def stop(self) -> float:
		if self.rank == 0:
			delta = default_timer() - self.overall_start
			self.accrued['overall'] = delta
			return delta
		return 0

	def print(self):
		if self.rank == 0:
			secs = np.array(list(self.accrued.values()))[:, np.newaxis]
			perc = secs / self.accrued['overall']
			data = np.hstack([secs, perc])
			df = pd.DataFrame(data=data, columns=['Seconds', 'Fraction'], index=list(self.accrued.keys()))
			logger.print(df)

global_timer = Timer()