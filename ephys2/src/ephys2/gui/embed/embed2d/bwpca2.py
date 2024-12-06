'''
Multimodality-weighted PCA embedding of wavelet-denoised waveforms
'''

import numpy as np
import numpy.typing as npt
import scipy.stats as stats

from .wpca2 import *

class BWPCA2Widget(WPCA2Widget):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._beta = 1
		self._beta_edit = QtWidgets.QLineEdit()
		self._beta_edit.setText(str(self._beta))
		self._beta_edit.returnPressed.connect(self._setBeta)
		self._axWidget._layout.addWidget(QtWidgets.QLabel('Beta:'))
		self._axWidget._layout.addWidget(self._beta_edit)

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		N = X.shape[0]
		if N > 0:
			k = X.shape[1] // 4
			X_ = X.reshape((N, 4, k)).reshape((N * 4, k))
			X_ = beta_truncated_dwt(X_, self._wvt, self._beta)
			M = X_.shape[1]
			X_ = X_.reshape((N, 4, M)).reshape((N, 4 * M))
			Y = self._pca.fit_transform(X_)
		else:
			Y = X
		return Y[:, axis1], Y[:, axis2]

	def _setBeta(self):
		self._beta = validate_float(self._beta_edit.text(), 1, np.inf)
		self._updatePlot()