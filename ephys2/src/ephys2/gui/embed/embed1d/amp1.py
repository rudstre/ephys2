'''
Widget for embedding in peak-amplitude space
'''
import numpy as np
import numpy.typing as npt
import pdb

from .base import *

class Amp1Widget(Embed1dWidget):
	'''
	Assumes a tetrode geometry.
	'''
	n_channels: int = 4

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			'All channels  ': Amp1Widget.n_channels # Take peak across all channels
		} | {
			f'Channel {i+1}  ': i
			for i in range(Amp1Widget.n_channels)
		}

	def embed(self, data: VBatch, axis: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		N = X.shape[0]
		M = X.shape[1] // self.n_channels
		if axis < self.n_channels:
			chan = X[:, axis*M:(axis + 1)*M]
			y = chan[np.arange(N), np.abs(chan).argmax(axis=1)]
		else:
			y = X[np.arange(N), np.abs(X).argmax(axis=1)]
		assert data.time.shape == y.shape
		return data.time, y
