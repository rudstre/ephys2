'''
Widgets for visualizing 2D t-SNE.
'''

import numpy as np
import numpy.typing as npt
from sklearn.manifold import TSNE

from .base import *

class TSNE2Widget(Embed2dWidget):
	def __init__(self, *args, **kwargs):
		self._tsne = TSNE(n_components=2, learning_rate='auto', init='pca')

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			'Component 1': 0,
			'Component 2': 1,
		}

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		if X.shape[0] > 0:
			if X.shape[0] == 1:
				X = np.vstack((X, X))
				Y = self._tsne.fit_transform(X)
				Y = Y[0][np.newaxis]
			else:
				Y = self._tsne.fit_transform(X)
		return Y[:, axis1], Y[:, axis2]

	