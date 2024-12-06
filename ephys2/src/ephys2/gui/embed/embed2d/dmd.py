'''
2D embedding by projection onto leading DMD modes
'''

import numpy as np
import numpy.typing as npt
from pydmd import DMD, MrDMD, HODMD
from sklearn.decomposition import PCA
import math

from .base import *

class DMDWidget(Embed2dWidget):
	n_components: int = 2

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Component {i+1}  ': i 
			for i in range(DMDWidget.n_components)
		}

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		N = X.shape[0]
		if N > 0:
			k = X.shape[1] // 4
			X_ = X.reshape((N, 4, k)).reshape((N * 4, k))
			dmd = HODMD(svd_rank=0, exact=True, opt=True, d=2, rescale_mode='auto')
			dmd.fit(X_)
			eabs = np.abs(dmd.eigs)
			eabs.sort()
			eabs = eabs[::-1]
			_, eidx = np.unique(eabs, return_index=True)
			dynamics = dmd.dynamics[eidx].real
			nmodes = dynamics.shape[0]
			power = X_ @ dynamics.T
			Y = power.reshape((N, 4, nmodes)).sum(axis=1)
			assert Y.shape == (N, nmodes)
		else:
			Y = X
		return Y[:, axis1], Y[:, axis2]

