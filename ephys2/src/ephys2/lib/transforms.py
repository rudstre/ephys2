'''
Feature transforms
Do not import any ephys2 libraries; this module is a root.
'''

import numpy as np
import numpy.typing as npt
import scipy.stats as stats
import pywt
from typing import Optional
# from cr.sparse import lop


def multimodality_weighted(X: npt.NDArray[np.float32], axis=0) -> npt.NDArray[np.float32]:
	'''
	Kolmogorov-Smirnov based multimodality weighting scheme described in 
	https://www.frontiersin.org/articles/10.3389/fninf.2012.00005/full
	'''
	assert len(X.shape) == 2
	N = X.shape[0]
	X_ = (X - np.median(X, axis=axis)) / madev(X, axis=axis) # Rescaled by madev
	X_s = np.sort(X, axis=axis) # 1D-sorted data
	idx = np.arange(1, N+1)[:, np.newaxis]
	mw =  np.abs(idx / (N + 1) - stats.norm.cdf(X_s)).max(axis=axis) # multimodal weights
	X_mw = X_ * mw / np.linalg.norm(X_, axis=axis)
	assert X_mw.shape == X.shape
	return X_mw

def madev(X: npt.NDArray, axis=0):
	''' 
	Median absolute deviation of a signal 
	'''
	return np.median(np.absolute(X - np.median(X, axis=axis)), axis=axis) * 1.4826

def beta_weighted(X: npt.NDArray, beta: float) -> npt.NDArray:
	'''
	Return a Beta-distribution weighted set of feature vectors 
	N samples x M features
	'''
	assert len(X.shape) == 2
	return X * stats.beta.pdf(np.linspace(0, 1, X.shape[1]), beta, beta)

def truncated_dwt(X: npt.NDArray, wavelet: str, mode='zero') -> npt.NDArray:
	'''
	Wavelet transform with zeroed detail coefficients (1-level)
	'''
	assert len(X.shape) == 2
	return pywt.dwt(X, wavelet, mode=mode, axis=1)[0]

def truncated_dwt2(X: npt.NDArray, wavelet: str, level: int=2, mode='zero') -> npt.NDArray:
	'''
	Wavelet transform with zeroed detail coefficients (2-level)
	'''
	assert len(X.shape) == 2
	return pywt.wavedec(X, wavelet, level=level, mode=mode, axis=1)[0]

# def truncated_dwt2(X: npt.NDArray, wavelet: str, level: int=2, trunc_level: int=2) -> npt.NDArray:
# 	'''
# 	Wavelet transform with truncated coefficients using the explicit operator
# 	'''
# 	assert len(X.shape) == 2
# 	M = X.shape[1]
# 	DWT_op = lop.dwt(M, wavelet, level=level)
# 	X = DWT_op.times(X.T).__array__().T
# 	assert X.shape[1] == M
# 	M = X.shape[1] // trunc_level
# 	X = X[:, :M]
# 	return X

def beta_truncated_dwt(X: npt.NDArray[np.float32], wavelet: Optional[str], beta: float) -> npt.NDArray[np.float32]:
	'''
	Beta-weighted truncated discrete wavelet transform
	'''
	assert len(X.shape) == 2
	assert beta >= 1
	if beta > 1:
		X = beta_weighted(X, beta)
	if wavelet != None:
		X = truncated_dwt(X, wavelet)
	return X
