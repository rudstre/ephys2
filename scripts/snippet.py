'''
Quick-n-dirty script for snippeting.

Assumes the data representation: M channels x N samples matrix.
'''

import numpy as np
import scipy.signal as sg

from rhd2df import rhd2df

def bandpass(ch: np.ndarray, padding: int, lo: float, hi: float) -> np.ndarray:
	b, a = sg.ellip(4, 1, 100, (lo, hi), btype='bandpass', output='ba')
	ch = sg.filtfilt(b, a, ch, padtype=None, padlen=0)
	return ch[:, padding:-padding]

def median_filter(ch: np.ndarray) -> np.ndarray:
	return ch - np.median(ch, axis=0)

def thresh_detect(tetr: np.ndarray) -> np.ndarray: 
	pass

def snippet_at(tetr: np.ndarray, times: np.ndarray) -> np.ndarray:
	pass