'''
IIR Filter algorithms using second-order sections

References:
https://www.digikey.com/en/articles/the-basics-of-anti-aliasing-low-pass-filters#:~:text=These%20filters%20must%20band%20limit,sharply%20above%20the%20Nyquist%20frequency.

'''

import numpy as np
import numpy.typing as npt
import scipy.signal as signal

from ephys2.lib.types import *
from .base import *
	
''' 
Bandpass filter 
(Configurable as highpass, lowpass, or bandpass depending on critical frequencies)
'''

class BandpassStage(PreprocessingStage):

	@staticmethod
	def name() -> str:
		return 'bandpass'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'order': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Filter order; increase to obtain better filter response, at the expense of performance and numerical stability and artifacts'
			),
			'highpass': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'Hz',
				description = 'Highpass filter frequency; set to 0 to disable'
			),
			'lowpass': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'Hz',
				description = 'Lowpass filter frequency; set to inf to disable'
			),
			'Rp': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'dB',
				description = 'Maximum ripple in the passband'
			),
			'Rs': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'dB',
				description = 'Minimum attenuation in the stopband'
			),
			'type': CategoricalParameter(
				categories = ['ellip', 'cheby1', 'cheby2','butter'],
				units = None,
				description = 'Filter type'
			),
			'padding_type': CategoricalParameter(
				categories = ['odd', 'even'],
				units = None,
				description = 'Signal extension method for suppressing boundary artifacts'
			),
			'padding_length': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'samples',
				description = 'Signal extension length'
			),
		}

	def initialize(self):
		self.sos = None

	def process(self, data: SBatch) -> SBatch:
		if data.size > 0:
			if self.cfg['lowpass'] < np.inf or self.cfg['highpass'] > 0:
				if self.sos is None:
					# Only design once; need sampling rate
					critical_freqs = []
					btype = None
					if self.cfg['highpass'] > 0:
						critical_freqs.append(self.cfg['highpass'])
						btype = 'highpass'
					if self.cfg['lowpass'] < data.fs / 2: # Cannot design a digital lowpass higher than Nyquist limit
						critical_freqs.append(self.cfg['lowpass'])
						btype = 'lowpass'
					if len(critical_freqs) == 2:
						btype = 'bandpass'

					self.sos = signal.iirfilter(
						self.cfg['order'],
						critical_freqs,
						rp=self.cfg['Rp'],
						rs=self.cfg['Rs'],
						btype=btype,
						analog=False,
						ftype=self.cfg['type'],
						output='sos',
						fs=data.fs
					).astype(np.float32)

				data.data = signal.sosfiltfilt(
					self.sos, 
					data.data,
					axis=0,
					padtype=self.cfg['padding_type'],
					padlen=min(self.cfg['padding_length'], data.size-1)
				)

		return data
