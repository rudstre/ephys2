'''
Waveform generators based on Jeremy Magland's code
https://github.com/magland/spikeforest/blob/master/gen_synth_datasets/8trode
'''

import numpy as np
import numpy.typing as npt
import scipy

MeanStd = Tuple[float, float]

def generate_waveform_library(
		N_wv: int, 																# Number of waveforms to generate
		fs: int,																	# Sampling rate (Hz)
		excitation: MeanStd, 											# Peak amplitude of excitation phase (uV)				
		depolarization: MeanStd,									# Peak amplitude of depolarization phase (uV)									
		repolarization: MeanStd, 									# Peak amplitude of repolarization phase (uV)
		exc_period: MeanStd, 											# Period of excitation phase (ms)
		dep_period: MeanStd, 											# Period of depolarization phase (ms)
		rep_period: MeanStd, 											# Period of repolarization phase (ms)
		ref_period: MeanStd, 											# Period of refractory phase (ms)
		sign: Optional[int]=None,									# Sign: up- or down-firing
	) -> npt.NDArray[np.float32]:
	'''
	Generate a library of spike waveforms from a parametric distribution involving:
	* amplitude
	* duration

	Assumes the signal starts & ends at 0.
	'''
	exc_a = np.random.normal(loc=excitation[0], scale=excitation[1], size=N)
	dep_a = np.random.normal(loc=depolarization[0], scale=depolarization[1], size=N)
	rep_a = np.random.normal(loc=repolarization[0], scale=repolarization[1], size=N)
	exc_p = np.clip(np.random.normal(loc=exc_period[0], scale=exc_period[1], size=N), 0, None)
	dep_p = np.clip(np.random.normal(loc=dep_period[0], scale=dep_period[1], size=N), 0, None)
	rep_p = np.clip(np.random.normal(loc=rep_period[0], scale=rep_period[1], size=N), 0, None)
	ref_p = np.clip(np.random.normal(loc=ref_period[0], scale=ref_period[1], size=N), 0, None)
	if sign is None:
		sign = random.randint(0, 1, size=N) * 2 - 1 # Randomize up- or down-firing

	exc_n = (fs * exc_p / 1000).round().astype(int)
	dep_n = (fs * dep_p / 1000).round().astype(int)
	rep_n = (fs * rep_p / 1000).round().astype(int)
	ref_n = (fs * ref_p / 1000).round().astype(int)
	mid_n = (exc_n + dep_n).max()
	end_n = (rep_n + ref_n).max()
	total_n = mid_n + end_n

	wv = np.zeros((N_wv, total_n), dtype=np.float32)

	eps = 0.001 # Initial perturbation
	x0 = eps * sign

	# wv[:, :exc_n] = 

	# if amps_mu is None:
	# 	amps_mu = np.array([0.5, 10, 1, 0])
	# if phases_mu is None:
	# 	phases_mu = np.array([200, 10, 30, 200]) / 440
	# assert amps_mu.size == phases_mu.size == 4
	# assert (amps_mu >= 0).all()
	# assert (phases_mu >= 0).all()
	# assert phases_mu.sum() == 1
	# assert M_real > 0
	# assert M_samples <= M_real



	x_real = np.linspace(0, 1, M_real)
	sign = random.randint(0, 1) * 2 - 1 # Randomize up- or down-firing

if __name__ == '__main__':
	import matplotlib.pyplot as plt
