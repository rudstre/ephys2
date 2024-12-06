'''
Zero out channels
'''

import numpy as np
import pdb

from ephys2.lib.types import *
from .base import *

class SetZeroStage(PreprocessingStage):

	@staticmethod
	def name() -> str:
		return 'set_zero'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'channels': ListParameter(
				element = IntParameter(start=0, stop=np.inf, units=None, description=''),
				units = None,
				description = 'Channels to set to zero (zero-indexed)'
			),
		}

	def initialize(self):
		self.chs = np.array(self.cfg['channels'], dtype=np.int64)

	def process(self, data: SBatch) -> SBatch:
		data.data[:,self.chs] = 0
		return data
