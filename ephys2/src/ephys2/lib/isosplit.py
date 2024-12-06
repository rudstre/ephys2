'''
Python interface to ISO-SPLIT
https://github.com/flatironinstitute/isosplit5
'''

from typing import Optional
import numpy as np
import numpy.typing as npt
import pdb
from sklearn.decomposition import PCA

from ephys2.lib.cluster import *
from ephys2.lib.singletons import logger
import ephys2._cpp as _cpp

def isosplit5(
		X: npt.NDArray[np.float32],
		n_components: int = 10,
		isocut_threshold: Optional[float]=1.0,
		min_cluster_size: Optional[int]=10,
		K_init: Optional[int]=200,
		refine_clusters: Optional[bool]=False,
		max_iterations_per_pass: Optional[int]=500,
		random_seed: Optional[int]=None, # Random seed
		jitter: float=0, # Random jitter to apply to suppress matrix inversion errors
		model: Optional[PCA]=None,
	) -> Labeling:
	# Add independent noise to stabilize matrix inversion in iso-split
	if jitter > 0:
		rng = np.random.default_rng(seed=random_seed)
		X += rng.normal(loc=0, scale=jitter, size=X.shape)
	m = min(min(X.shape), n_components)
	# Resize embedding suitable for input
	if model is None or model.n_components > m:
		model = PCA(n_components=m, svd_solver='randomized', random_state=random_seed)
	Y = model.fit_transform(X)
	Y = Y.T.astype(np.float32, order='F') # cpp lib requires Fortran order
	labels = np.zeros(Y.shape[1]).astype(np.int32)
	_cpp.isosplit5(Y, labels, isocut_threshold, min_cluster_size, K_init, refine_clusters, max_iterations_per_pass, random_seed)
	return labels

def isosplit5_pca_branch(
		X: npt.NDArray[np.float32],
		n_components: int=10,
		isocut_threshold: Optional[float]=1.0,
		min_cluster_size: Optional[int]=10,
		K_init: Optional[int]=200,
		refine_clusters: Optional[bool]=False,
		max_iterations_per_pass: Optional[int]=500,
		jitter: float=0, # Random jitter to apply to suppress matrix inversion errors
		random_seed: Optional[int]=None # Random seed
	) -> Labeling:
	'''
	Computes a "stable" clustering by recursively applying PCA / ISOSPLIT 
	in the manner described in https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5743236/
	'''
	model = PCA(n_components=n_components, svd_solver='randomized', random_state=random_seed)
	N = X.shape[0]

	clusters_queue = [np.arange(N)]
	final_clustering = []

	# Recursively cluster using the "branch" method
	while len(clusters_queue) > 0:
		cluster = clusters_queue.pop()
		if cluster.size <= 1:
			final_clustering.append(cluster)
		else:
			lb = isosplit5(
				X[cluster],
				n_components = n_components,
				isocut_threshold = isocut_threshold,
				min_cluster_size = min_cluster_size,
				K_init = K_init,
				refine_clusters = refine_clusters,
				max_iterations_per_pass = max_iterations_per_pass,
				jitter = jitter, 
				random_seed = random_seed,
				model = model
			)
			clustering = labeling_to_clustering(lb, indices=cluster)
			if len(clustering) == 1:
				final_clustering.append(clustering[0])
			else:
				clusters_queue.extend(clustering)

	labeling, _ = clustering_to_labeling(final_clustering, N)
	return labeling

