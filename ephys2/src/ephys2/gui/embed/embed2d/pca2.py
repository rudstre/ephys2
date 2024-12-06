'''
Widgets for visualizing 2D PCA.
'''

import numpy as np
import numpy.typing as npt
from sklearn.decomposition import PCA
import math
from sklearn.preprocessing import StandardScaler

from .base import *

class PCA2Widget(Embed2dWidget):
	n_components: int = 5

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._pca = PCA(n_components=self.n_components)

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Component {i+1}  ': i 
			for i in range(PCA2Widget.n_components)
		}

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		N = X.shape[0]
		if N > 0:
			if N < self.n_components:
				n_repeat = math.ceil(self.n_components / N)
				X_ = np.repeat(X, n_repeat, axis=0)
				Y = self._pca.fit_transform(X_)
				Y = Y[:N][np.newaxis]
			else:
				X_ = StandardScaler().fit_transform(X)
				Y = self._pca.fit_transform(X_)
		else:
			Y = X
		return Y[:, axis1], Y[:, axis2]

