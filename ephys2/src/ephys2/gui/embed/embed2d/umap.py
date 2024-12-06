'''
Dimensionality reduction using UMAP
'''
import umap

import numpy as np
import numpy.typing as npt
import umap
from sklearn.preprocessing import StandardScaler
import math

from .base import *

class UMAPWidget(Embed2dWidget):
	n_components: int = 5

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Component {i+1}  ': i 
			for i in range(UMAPWidget.n_components)
		}

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		N = X.shape[0]
		if N > 0:
			X_ = StandardScaler().fit_transform(X)
			reducer = umap.UMAP(n_components=self.n_components)
			Y = reducer.fit_transform(X_)
		else:
			Y = X
		return Y[:, axis1], Y[:, axis2]

