'''
Decimate (filter and downsample) a signal by Chebyshev type I filter

Wraps:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.decimate.html
'''

import numpy as np
import numpy.typing as npt
import scipy.signal as signal

from ephys2.lib.types import *
from .base import *
	
class DecimateStage(PreprocessingStage):

	@staticmethod
	def name() -> str:
		return 'decimate'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'order': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Filter order; increase to obtain better filter response, at the expense of performance and numerical stability and artifacts'
			),
			'factor': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Downsampling factor. "When using IIR downsampling, it is recommended to call decimate multiple times for downsampling factors higher than 13" - scipy'
			),
			'type': CategoricalParameter(
				categories = ['iir', 'fir'],
				units = None,
				description = 'Filter type, infinite impulse response (iir) or finite impulse response (fir)'
			),
		}

	def process(self, data: SBatch) -> SBatch:
		data.fs = data.fs // self.cfg['factor']
		if data.size > 0:
			data.time = data.time[::self.cfg['factor']]
			data.data = signal.decimate(
				data.data, 
				self.cfg['factor'], 
				n=self.cfg['order'],
				ftype=self.cfg['type'], 
				zero_phase=True,
				axis=0, 
			)
		return data