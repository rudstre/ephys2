'''
2d blobs benchmark
'''

from typing import Tuple, Dict
import numpy as np
import numpy.typing as npt
import sklearn
import sklearn.datasets
import sklearn.cluster

from .base import ClusterBenchmark
from ephys2.lib.spc import *
from ephys2.lib.isosplit import isosplit5

class CirclesBenchmark(ClusterBenchmark):
	cluster_std = [1.0, 2.5, 0.5, 0.66, 0.75, 1]

	def get_data_and_ground_truth(self) -> Tuple[npt.NDArray[float], npt.NDArray[np.int64]]:
		return sklearn.datasets.make_blobs(n_samples=1000, centers=len(self.cluster_std), cluster_std=self.cluster_std, random_state=170)

	def run_algorithms(self, X: npt.NDArray[float]) -> Dict[str, npt.NDArray[np.int64]]:
		spc_temps, spc_clusterings =  run_spc(
			X, 0.01, 0.10, 3, 300, 11, random_seed=0
		)

		result = {
			'K-means': sklearn.cluster.KMeans(n_clusters=len(self.cluster_std)).fit_predict(X),
			'DBScan (eps=0.3)': sklearn.cluster.DBSCAN(eps=0.4, min_samples=5).fit_predict(X),
			'ISO-SPLIT': isosplit5(X),
		}

		for (temp, clustering) in zip(spc_temps, spc_clusterings):
			result[f'SPC (T={temp:.{4}g})'] = clustering

		return result 

	def embed_2d(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		return X

if __name__ == '__main__':
	np.random.seed(0)
	CirclesBenchmark().run()
