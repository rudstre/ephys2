'''
Test stage for generating integers in sequence.
'''

import numpy as np
from typing import Optional
import time
import random

from ephys2.lib.types import *
from ephys2.pipeline.input.base import *

class IntegersStage(InputStage):

	@staticmethod
	def name() -> str:
		return 'integers'

	def output_type(self) -> type:
		return int

	@staticmethod
	def parameters() -> Parameters:
		return {
			'start': IntParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Start integer'
			),
			'stop': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Stop integer'
			),
		}

	def initialize(self):
		self.ctr = self.cfg['start'] + self.rank

	def produce(self) -> Optional[int]:
		val = self.ctr
		# time.sleep(random.randint(1, 10) * 0.001)
		if val < self.cfg['stop']:
			self.ctr += self.n_workers
			return val


