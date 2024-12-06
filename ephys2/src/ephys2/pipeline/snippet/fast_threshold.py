'''
FAST snippeting algorithms
'''

from typing import Tuple
import numpy as np
import pdb

import ephys2._cpp as _cpp
from ephys2.lib.types import *
from .base import *

class FastThresholdStage(SnippetingStage):

	@staticmethod
	def name() -> str:
		return 'fast_threshold'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'snippet_length': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Detected waveform length'
			),
			'detect_threshold': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'μV',
				description = 'Absolute threshold any channel must cross to trigger spike detection'
			),
			'return_threshold': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'μV',
				description = 'Absolute threshold all channels must return under to trigger spike completion'
			),
			'return_samples': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Minimum time spike must remain below return threshold to consider completed'
			),
			'n_channels': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of channels per channel group (e.g. 4 for tetrode)',
			),
		}

	def process(self, amp_data: SBatch) -> VMultiBatch:
		'''
		Threshold-based snippeting of tetrode array
		'''
		all_times, all_features, max_length = _cpp.snippet_channel_groups(
			amp_data.time,
			amp_data.data,
			self.cfg['snippet_length'],
			self.cfg['detect_threshold'],
			self.cfg['return_threshold'],
			self.cfg['return_samples'],
			self.cfg['n_channels']
		)

		return VMultiBatch(
			items = {
				str(i): VBatch(
					time = time,
					data = data,
					overlap = 0, # TODO: how to convert overlap in source data to output data? (We currently assume source overlap is minimal such that event overlaps cannot occur)
				) for i, (time, data) in enumerate(zip(all_times, all_features))
			},
		)
