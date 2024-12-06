'''
Plot amplifier data from raw electrode recordings
'''

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import colorcet as cc
import math
from numpy import ndarray

from .plot_utils import signalplot

def plot_tetrodes(
		amp_t: ndarray, 
		amp_data: ndarray,
		thr: Tuple[float, float]=None # (lo, hi) thresholds to plot
	): 
	'''
	Plots the data assuming a tetrode layout.
	'''
	M = amp_data.shape[1]
	assert (M % 4 == 0), 'Data is not a tetrode array'
	
	fig, axs = signalplot(M)

	zeros = np.zeros_like(amp_t)
	if thr != None:
		lo = thr[0] * np.ones_like(amp_t)
		hi = thr[1] * np.ones_like(amp_t)
	for c in range(M):
		axs[c].margins(x=0)
		axs[c].plot(amp_t, zeros, color='black')
		axs[c].plot(amp_t, amp_data[:, c], color=cc.glasbey[c//4])
		if thr != None:
			axs[c].plot(amp_t, lo, color='red')
			axs[c].plot(amp_t, -lo, color='red')
			axs[c].plot(amp_t, hi, color='green')
			axs[c].plot(amp_t, -hi, color='green')
		axs[c].yaxis.set_visible(False)
