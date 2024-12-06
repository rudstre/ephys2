'''
2d blobs benchmark
'''

from typing import Tuple, Dict
import random
import numpy as np
import numpy.typing as npt
import sklearn
import sklearn.datasets
import sklearn.cluster

from .base import TrackingBenchmark

from ephys2.lib.types import *
from ephys2.pipeline.label_old.spc_segfuse import SPCSegFuseStage

class Benchmark(TrackingBenchmark):
	eps_perturb: float = 0.  # Maximum coordinate-wise perturbation

	def get_data_and_ground_truth(self) -> Tuple[npt.NDArray[float], npt.NDArray[np.int64]]:
		return sklearn.datasets.make_blobs(n_samples=1000, centers=3, random_state=42, cluster_std=1)

	def perturb_data(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		dX = self.eps_perturb * np.clip(np.random.randn(X.shape[1]), -1, 1)
		return X + dX[np.newaxis, :]

	def run_algorithms(self, 
			X1: npt.NDArray[np.float32], 	# Dataset 1
			X2: npt.NDArray[np.float32]		# Dataset 2 (should be temporally adjacent to 1)
		) -> Dict[str, LinkedLabeling]:
		N, M = X1.shape
		X = np.concatenate((X1, X2), axis=0)

		make_spc_stage = lambda tmax: SPCSegFuseStage({
			'block_size': N,
			't_min': 0,
			't_max': tmax,
			'n_temps': 11,
			'knn': 11,
			'cycles': 300,
			'metric': 'euclidean',
			'link_threshold': 0.02,
			'link_sig_s': 0.005,
			'link_sig_k': 0.03,
		}, VMultiBatch)

		result = {
			'spc_segfuse (tmax: 0.001)': make_spc_stage(0.001).label_and_link(X, 0),
			'spc_segfuse (tmax: 0.01)': make_spc_stage(0.01).label_and_link(X, 0),
			'spc_segfuse (tmax: 0.1)': make_spc_stage(0.1).label_and_link(X, 0),
		}

		return result 

	def embed_2d(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		return X

if __name__ == '__main__':
	random.seed(0)
	np.random.seed(0)
	Benchmark().run()
