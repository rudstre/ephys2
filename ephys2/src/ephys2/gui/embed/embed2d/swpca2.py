'''
PCA embedding of wavelet-denoised waveforms
'''
import pywt

from .wpca2 import *

class SWPCA2Widget(WPCA2Widget):

	def embed(self, data: VBatch, axis1: int, axis2: int) -> Tuple[npt.NDArray, npt.NDArray]:
		X = data.data
		assert len(X.shape) == 2
		N = X.shape[0]
		if N > 0:
			k = X.shape[1] // 4
			X_ = X.reshape((N, 4, k)).reshape((N * 4, k))
			[(cA, cD)] = pywt.swt(X_, self._wvt, level=1, axis=1)
			ncoeffs = cA.shape[1]
			cA = cA.reshape((N, 4, ncoeffs)).reshape((N, 4 * ncoeffs))
			Y = self._pca.fit_transform(cA)
		else:
			Y = X
		return Y[:, axis1], Y[:, axis2]

