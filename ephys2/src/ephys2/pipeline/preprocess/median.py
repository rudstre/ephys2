'''
Median filtering
'''

import numpy as np
import pdb

from ephys2.lib.types import *
from .base import *

class MedianFilterStage(PreprocessingStage):

	@staticmethod
	def name() -> str:
		return 'median_filter'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'group_size': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Size of channel group (contiguous) over which to subtract median'
			),
			'ignore_channels': ListParameter(
				element = IntParameter(start=0, stop=np.inf, units=None, description=''),
				units = None,
				description = 'Channels to exclude from median calculation (zero-indexed)'
			),
		}

	def initialize(self):
		self.input_selectors = dict()
		self.ignore_channels = set(self.cfg['ignore_channels'])

	def process(self, data: SBatch) -> SBatch:
		'''
		Median filter per-group (assumes group channels are contiguous)
		'''
		assert data.data.shape[1] % self.cfg['group_size'] == 0, 'Median group size not a divisor of # channels'

		if self.input_selectors is None:
			for group in range(data.data.shape[1]//self.cfg['group_size']):
				c_s, c_e = group*self.cfg['group_size'], (group+1)*self.cfg['group_size']

		for group in range(data.data.shape[1]//self.cfg['group_size']):
			c_s, c_e = group*self.cfg['group_size'], (group+1)*self.cfg['group_size']
			if not (group in self.input_selectors):
				if any((c_s <= c < c_e) for c in self.ignore_channels):
					self.input_selectors[group] = np.array([c for c in range(c_s, c_e) if not (c in self.ignore_channels)], dtype=np.int64)
				else:
					self.input_selectors[group] = slice(c_s, c_e)

			data.data[:, c_s:c_e] -= np.median(data.data[:, self.input_selectors[group]], axis=1)[:,np.newaxis]

		return data
