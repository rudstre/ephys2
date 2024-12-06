'''
Widget for embedding in L2 norm space
'''
import numpy as np
import numpy.typing as npt
import pdb

from .base import *

class EnergyWidget(Embed1dWidget):
	'''
	Assumes a tetrode geometry.
	'''
	n_channels: int = 4

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Channel {i+1}  ': i
			for i in range(EnergyWidget.n_channels)
		} | {
			'All channels  ': EnergyWidget.n_channels # Take peak across all channels
		}

	def embed(self, data: VBatch, axis: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		N = X.shape[0]
		M = X.shape[1] // self.n_channels
		if axis < self.n_channels:
			chan = X[:, axis*M:(axis + 1)*M]
			y = np.linalg.norm(chan, axis=1)
		else:
			y = np.linalg.norm(X, axis=1)
		assert data.time.shape == y.shape
		return data.time, y
