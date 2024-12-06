'''
Plot snippet data
'''

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import colorcet as cc
import math
from numpy import ndarray

from ephys2.lib.types import *
from .plot_utils import signalplot

def plot_tetrode_snippets(
		amp_t: ndarray,
		w_t: ndarray, 
		w_tetr: ndarray,
		w_data: ndarray,
		N_tetr: int,
		thr: Tuple[float, float]=None # (lo, hi) thresholds to plot
	): 
	'''
	Plots snippet data assuming a tetrode layout.
	'''
	N = w_t.shape[0]
	M = N_tetr * 4
	s_len = w_data.shape[1] // 4

	fig, axs = signalplot(M)

	zeros = np.zeros_like(amp_t)

	if thr != None:
		lo = thr[0] * np.ones_like(t)
		hi = thr[1] * np.ones_like(t)

	for c in range(M):
		axs[c].plot(amp_t, zeros, color='black')
		axs[c].yaxis.set_visible(False)

	for w_i in range(N):
		tetr = w_tetr[w_i]
		start = w_t[w_i] - s_len//2
		window = np.arange(start, start+s_len)
		for c in range(4):
			waveform = w_data[w_i, s_len*c:s_len*(c+1)]
			k = tetr*4 + c
			axs[k].plot(window, waveform, color=cc.glasbey[tetr])
			axs[k].axvline(x=w_t[w_i], color='red')
			axs[k].axvline(x=window[0], color='black')
			axs[k].axvline(x=window[-1], color='black')

def plot_snippets(
		snippets: ndarray,
		thr: Tuple[float, float]=None # (lo, hi) thresholds to plot
	):
	
	N = snippets.shape[0]
	t = np.arange(snippets.shape[1])
	fig, axs = signalplot(N)
	zeros = np.zeros_like(t)

	if thr != None:
		lo = thr[0] * np.ones_like(t)
		hi = thr[1] * np.ones_like(t)

	for i in range(N):
		axs[i].plot(t, zeros, color='black')
		axs[i].plot(t, snippets[i], color=cc.glasbey[i])
		if thr != None:
			axs[i].plot(t, lo, color='red')
			axs[i].plot(t, -lo, color='red')
			axs[i].plot(t, hi, color='green')
			axs[i].plot(t, -hi, color='green')
		axs[i].yaxis.set_visible(False)
