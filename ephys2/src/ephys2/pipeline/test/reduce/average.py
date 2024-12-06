'''
Compute the average of n numbers in parallel.
'''

import numpy as np

from ephys2.lib.mpi import MPI
from ephys2.lib.types import *
from ephys2.lib.singletons import logger

class AverageStage(ReductionStage):

	@staticmethod 
	def name() -> str:
		return 'average'

	def type_map(self) -> Dict[type, type]:
		return {int: int}

	def initialize(self):
		self.count = 0
		self.value = 0

	def process(self, data: int) -> int:
		# Compute counts, values within this process
		self.count += 1
		self.value += data
		return data

	def reduce(self):
		# Compute counts, values across all processes
		counts = self.comm.gather(self.count, root=0)
		values = self.comm.gather(self.value, root=0)
		if self.rank == 0:
			avg = sum(values) / sum(counts)
			logger.print(f'Final average: {avg}')