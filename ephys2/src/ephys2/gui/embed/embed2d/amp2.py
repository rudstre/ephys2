'''
Amplitude-vs-amplitude plots
'''

import numpy as np
import numpy.typing as npt
import pdb

from .base import *

class Amp2Widget(Embed2dWidget):
	'''
	Assumes a tetrode geometry.
	'''
	n_channels: int = 4

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Channel {i+1}  ': i
			for i in range(Amp2Widget.n_channels)
		}

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		N = X.shape[0]
		M = X.shape[1] // self.n_channels
		ch1 = X[:, axis1*M:(axis1 + 1)*M]
		ch2 = X[:, axis2*M:(axis2 + 1)*M]
		y1 = ch1[np.arange(N), np.abs(ch1).argmax(axis=1)]
		y2 = ch2[np.arange(N), np.abs(ch2).argmax(axis=1)]
		assert y1.shape == y2.shape
		return y1, y2

