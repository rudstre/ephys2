'''
Synthetic waveforms benchmark
'''

from typing import Tuple, Dict
import numpy as np
import numpy.typing as npt
import sklearn
import sklearn.datasets
import sklearn.cluster
import h5py
import pdb

from .base import ClusterBenchmark

from ephys2.lib.spc import *
from ephys2.pipeline.input.synthetic.utils import poisson_refr_superposition
from ephys2.lib.cluster import clustering_to_labeling
from ephys2.lib.isosplit import isosplit5

class WaveformBenchmark(ClusterBenchmark):
	n_units = 3
	min_firing_rate = 0.1
	max_firing_rate = 1.0
	refractory_period = 1.5
	sampling_rate = 20000
	templates_file = 'tests/data/templates_50_tetrode_18-02-2022_19-52.h5'
	N = 1000
	noise_std = 1.0

	def get_data_and_ground_truth(self) -> Tuple[npt.NDArray[float], npt.NDArray[np.int64]]:
		rates = np.random.uniform(self.min_firing_rate, self.max_firing_rate, size=self.n_units)
		rng = np.random.default_rng(0)
		times, ids = poisson_refr_superposition(rng, rates, self.refractory_period, self.sampling_rate, self.N)
		with h5py.File(self.templates_file, 'r') as file:
			idxs = np.random.choice(file['templates'].shape[0], size=self.n_units)
			idxs.sort()
			units = file['templates'][idxs]
		spikes = units[ids]
		spikes = spikes.reshape(spikes.shape[0], spikes.shape[1] * spikes.shape[2]).astype(np.float32)
		spikes += np.random.normal(loc=0, scale=self.noise_std, size=spikes.shape)
		print(np.unique(ids))
		return spikes, ids

	def run_algorithms(self, X: npt.NDArray[float]) -> Dict[str, npt.NDArray[np.int64]]:
		# spc_temps, spc_clusterings = run_spc(
		# 	X, 0, 0.10, 11, 300, 11, random_seed=0
		# )
		spc_clustering = cluster_spc_multiround(
			X, 0, 0.10, 11, 300, 11, 1, 15, random_seed=0, n_rounds=4
		)
		spc_labeling, spc_K = clustering_to_labeling(spc_clustering, self.N)
		print(f'SPC found clusters: {spc_K}')

		result = {
			'K-means': sklearn.cluster.KMeans(n_clusters=3).fit_predict(X),
			'DBScan (eps=0.3)': sklearn.cluster.DBSCAN(eps=0.4, min_samples=5).fit_predict(X),
			'SPC': spc_labeling,
			'ISO-SPLIT': isosplit5(X),
		}

		# for (temp, clustering) in zip(spc_temps, spc_clusterings):
		# 	result[f'SPC (T={temp:.{4}g})'] = clustering

		return result 

	def embed_2d(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		K = X.shape[1] // 4
		m1 = np.abs(X[:, :K]).max(axis=1)
		m2 = np.abs(X[:, K:2*K]).max(axis=1)
		X = np.hstack((m1[:, np.newaxis], m2[:, np.newaxis]))
		return X

if __name__ == '__main__':
	np.random.seed(0)
	WaveformBenchmark().run()
