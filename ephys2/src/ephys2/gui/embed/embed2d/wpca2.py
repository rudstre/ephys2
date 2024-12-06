'''
PCA embedding of wavelet-denoised waveforms
'''

import numpy as np
import numpy.typing as npt
from sklearn.decomposition import PCA
import math
import pywt

from ephys2.lib.transforms import *
from ephys2.gui.utils import *

from .base import *

class WPCA2Widget(Embed2dWidget):
	n_components: int = 5
	max_levels: int = 10

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Add wavelet selector
		self._wvt = 'sym2'
		self._lvl = 2
		self._wv_cb = pg.ComboBox()
		self._wv_cb.addItems(pywt.wavelist(kind='discrete'))
		self._wv_cb.setCurrentText(self._wvt)
		self._wv_cb.currentIndexChanged.connect(lambda _: self._setWavelet())
		self._lvl_cb = pg.ComboBox()
		self._lvl_cb.addItems([str(lvl) for lvl in range(self.max_levels)])
		self._lvl_cb.setCurrentText(str(self._lvl))
		self._lvl_cb.currentIndexChanged.connect(lambda _: self._setLevel())
		self._axWidget._layout.addWidget(QtWidgets.QLabel('Wavelet:'))
		self._axWidget._layout.addWidget(self._wv_cb)
		self._axWidget._layout.addWidget(QtWidgets.QLabel('Level:'))
		self._axWidget._layout.addWidget(self._lvl_cb)

		self._pca = PCA(n_components=self.n_components)

	@staticmethod
	def axisMap() -> Dict[str, int]:
		return {
			f'Component {i+1}  ': i 
			for i in range(WPCA2Widget.n_components)
		}

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		N = X.shape[0]
		if N > 0:
			k = X.shape[1] // 4
			X_ = X.reshape((N, 4, k)).reshape((N * 4, k))
			X_ = truncated_dwt(X_, self._wvt)
			M = X_.shape[1]
			X_ = X_.reshape((N, 4, M)).reshape((N, 4 * M))
			Y = self._pca.fit_transform(X_)
		else:
			Y = X
		return Y[:, axis1], Y[:, axis2]

	def _setWavelet(self):
		self._wvt = self._wv_cb.currentText()
		self._updatePlot()

	def _setLevel(self):
		self._lvl = int(self._lvl_cb.currentText())
		self._updatePlot()

