'''
Utilities for synthetic data generation
'''
from typing import Generator, Tuple
import numpy as np
import numpy.typing as npt
from scipy.stats import expon

def poisson_refr_superposition(
		rng: np.random.Generator, 		# RNG to synchronize / replicate
		rates: npt.NDArray[float], 		# Rates of each process (1 / E[seconds to produce 1 event])
		refr: float, 									# Refractory period (in ms)
		fs: int,											# Sampling rate (in Hz)
		N: int,												# Number of times to produce
	) -> Tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]:
	'''
	Generate arrival times from the superposition of K Poisson processes
	with absolute refractory periods. Rate corrections are performed
	to account for the refractory period, by solving:

	1/L_2 + refr = 1/L_1 (where L_1 is nominal rate and refr is the refractory period)

	Generates: (times, ids) where id is the process that fired
	'''
	K = rates.shape[0]
	refr /= 1000
	assert refr <= 1 / rates.max(), 'Refractory period must be smaller than the minimal arrival time'
	# Adjust rates for refractory period to achieve same mean rate
	adj_scales = (1 - rates * refr) / rates # (scale is inverse of rate, per scipy convention)
	# Interarrival times, ids of each process
	iats = rng.exponential(scale=adj_scales[np.newaxis], size=(N, K)) + refr
	# Convert arrival times to integer samples
	iats = np.round(iats * fs).astype(np.int64)
	# Accumulate into firing times
	times = np.cumsum(iats, axis=0)
	ids = np.repeat(np.arange(K)[np.newaxis], N, axis=0).astype(np.int64)
	# Sort and select final times
	times, ids = times.ravel(), ids.ravel()
	sel = np.argsort(times)[:N]
	return (times[sel], ids[sel])

def white_noise(
		N: int, 				# Number of samples
		sigma: float, 	# Standard deviation of white noise
	) -> npt.NDArray[np.float32]:
	'''
	Generate zero-centered white noise of a given standard deviation and length.
	'''
	assert sigma > 0
	return np.random.normal(0, sigma, N)

