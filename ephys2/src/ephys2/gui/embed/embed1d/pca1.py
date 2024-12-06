'''
Widget for embedding in principle component space
'''
import numpy as np
import numpy.typing as npt
from sklearn.decomposition import PCA

from .base import *

class PCA1Widget(Embed1dWidget):
	n_components: int = 5

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._pca = PCA(n_components=self.n_components)

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Component {i+1}  ': i 
			for i in range(PCA1Widget.n_components)
		}

	def embed(self, data: VBatch, axis: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		if X.shape[0] > 0:
			if X.shape[0] == 1:
				X = np.vstack((X, X))
				Y = self._pca.fit_transform(X)
				Y = Y[0][np.newaxis]
			else:
				Y = self._pca.fit_transform(X)
		else:
			Y = X
		return data.time, Y[:, axis]
