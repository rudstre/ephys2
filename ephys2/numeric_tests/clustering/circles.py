'''
2d concentric circles benchmark
'''

from typing import Tuple, Dict
import numpy as np
import numpy.typing as npt
import sklearn
import sklearn.datasets
import sklearn.cluster
import pdb

from .base import ClusterBenchmark
from ephys2.lib.spc import *
from ephys2.lib.isosplit import isosplit5

class Benchmark(ClusterBenchmark):

	def get_data_and_ground_truth(self) -> Tuple[npt.NDArray[float], npt.NDArray[np.int64]]:
		return sklearn.datasets.make_circles(n_samples=1000, factor=0.5, noise=0.05)

	def run_algorithms(self, X: npt.NDArray[float]) -> Dict[str, npt.NDArray[np.int64]]:
		spc_temps, spc_clusterings =  run_spc(
			X, 0.01, 0.10, 3, 300, 11, random_seed=0
		)

		result = {
			'K-means': sklearn.cluster.KMeans(n_clusters=2).fit_predict(X),
			'DBScan (eps=0.1)': sklearn.cluster.DBSCAN(eps=0.1, min_samples=5).fit_predict(X),
			'ISO-SPLIT': isosplit5(X),
		}

		for (temp, clustering) in zip(spc_temps, spc_clusterings):
			result[f'SPC (T={temp:.{4}g})'] = clustering

		# sim_thr = 1.05
		# spc_collapsed = collapse_labelings_to_clustering(
		# 	X, spc_clusterings, sim_thr
		# )

		# result[f'SPC (collapsed, thr={sim_thr})'] = clustering_to_labeling(X.shape[0], spc_collapsed)

		return result 

	def embed_2d(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		return X

if __name__ == '__main__':
	np.random.seed(0)
	Benchmark().run()
