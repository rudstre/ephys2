'''
SPC clustering functions

Other references:
* http://www.vcclab.org/lab/spc/
* https://gitlab.com/OlveczkyLab/Ehpys/-/tree/master/ephys_algos/SPC_protein_C%2B%2B
'''

import pdb
from typing import Tuple, Optional, Iterator
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from scipy.spatial.distance import cdist

from ephys2.lib.types import *
import ephys2._cpp


@dataclass
class SPCTree:
	cluster: Cluster
	children: List['SPCTree']

	def __len__(self) -> int:
		n = 0
		for _ in self.dfs():
			n += 1
		return n

	@staticmethod
	def construct(labelings: npt.NDArray[np.int64], indices: Optional[npt.NDArray[np.int64]]=None) -> 'SPCTree':
		'''
		Construct a tree from a sequence of cluster labelings.
		labelings: (K, L)-size array where K is the number of clustering runs and L is the number of samples clustered,
			containing the cluster labels. K is assumed ascending order of resolution (lowest first). 
		indices: (L,)-size array containing indices of each sample which is assigned the cluster label in `labelings`
		'''
		if indices is None:
			indices = np.arange(labelings.shape[1], dtype=np.int64)
		if labelings.shape[0] == 0:
			return SPCTree(children=[], cluster=indices)
		else:
			labeling = labelings[0]
			labels = np.unique(labeling)
			children = []
			for label in labels:
				where = labeling == label
				children.append(SPCTree.construct(
					labelings[1:, where],
					indices[where]
				))
			return SPCTree(
				cluster=indices,
				children=children
			)

	def merge(self, other: 'SPCTree'):
		'''
		Merges another tree; assumes the indices are disjoint.
		'''
		self.children.extend(other.children)
		self.cluster = np.concatenate((self.cluster, other.cluster))

	def is_leaf(self) -> bool:
		return self.children == []

	def dfs(self) -> Iterator['SPCTree']:
		'''
		Depth-first search iterator.
		'''
		def helper(node):
			yield node
			for c in node.children:
				yield from helper(c)

		yield from helper(self)

	def dfs_paths(self) -> Iterator[List[int]]:
		'''
		Iterate over paths from root to leaves.
		'''
		def helper(node, path):
			if node.is_leaf():
				yield path 
			else:
				for c in node.children:
					yield from helper(c, path + [c])
		yield from helper(self, [self])


def collapse_tree(tree: SPCTree, cluster_dist_threshold: float, samples: npt.NDArray[float]) -> Clustering:
	'''
	Collapse into a list of clusters. Should be called from the root (temperature=0) node. Mutates the tree.
	'''

	def cluster_dist(approximator: Cluster, approximatee: Cluster) -> float:
		'''
		cluster_dist between a cluster and its proposed approximator; not necessarily symmetric.
		(lower indicates more similar)
		'''
		xs = samples[approximatee]
		ys = xs - (samples[approximator].mean(axis=0)) # Distance from approximator average
		zs = xs - (xs.mean(axis=0)) # Distance from own average
		return np.sqrt(max(0, np.linalg.norm(ys)**2 - np.linalg.norm(zs)**2)) / samples.shape[1]

	def repartition(node: SPCTree) -> List[SPCTree]:
		'''
		Repartition a node and its children into a new set of children replacing the node.
		'''
		# Base case: node is the whole partition
		if node.is_leaf():
			return [node]

		separated = []
		remaining = []

		# Extract well-separated clusters
		for child in node.children:
			assert child.is_leaf()
			parent_dist = cluster_dist(node.cluster, child.cluster)
			if parent_dist > cluster_dist_threshold:
				separated.append(child)
			else:
				remaining.append(child)

		# Merge remaining into separated where possible
		merged = [] 												# Nodes to be merged together
		R = len(remaining)
		cross_distances = [np.inf] * R 			# Lowest distances to separated nodes
		cross_indices = [0] * R 						# Indices of lowest distances
		for i, node in enumerate(remaining): # Indexes L_i in step (3b)

			for j, other in enumerate(separated): # Indexes L_j in step (3b)
				cross_dist = cluster_dist(other.cluster, node.cluster)
				if cross_dist < cross_distances[i]:
					cross_distances[i] = cross_dist
					cross_indices[i] = j

			# Merge into a separated cluster
			if cross_distances[i] < cluster_dist_threshold:
				separated[cross_indices[i]].merge(node)

			# Merge into the self
			else:
				merged.append(node)

		# Merge the merge set
		N_merged = len(merged)
		if N_merged > 0:
			for i in range(1, N_merged):
				merged[0].merge(merged[i])
			separated.append(merged[0])

		return separated

	def collapse(node: SPCTree) -> List[SPCTree]:
		'''
		Recursively merge the tree
		'''
		leaves = []
		for child in node.children:
			if child.is_leaf():
				leaves.append(child)
			else:
				leaves.extend(collapse(child))

		node.children = leaves
		return repartition(node)

	return [node.cluster for node in collapse(tree)]

def cluster_spc_multiround(
		X: npt.NDArray[np.float64], 	# Input data (N_samples, M_features)
		Tmin: float, 									# Minimum temperature
		Tmax: float, 									# Maximum temperature
		Ntemps: int, 									# Number of temperatures to run, inclusive of the endpoints
		cycles: int, 									# No. cycles to run
		Knn: int, 										# K nearest neighbors to include in neighborhood
		cluster_dist_threshold: float,	# Similarity threshold at which to merge clusters (higher -> finer clustering); should be in same units as X
		min_cluster_size: int,				# Minimum cluster size
		MSTree: bool=True, 						# Whether to include minimum spanning tree edges 
		metric: str='euclidean', 			# Metric space (see scipy.spatial.distance.cdist for options)
		random_seed: Optional[int]=None, # Random seed
		n_rounds: int=1,								# Number of rounds to run successive clustering steps
	) -> Clustering:
	'''
	Run multiple rounds of cluster_spc, apply a cluster size cutoff criterion, and re-cluster outliers n times.
	Certain samples may not be present in any cluster due to cutoff criterion.
	'''
	assert n_rounds >= 1, 'Cannot run less than 1 round of clustering'

	N = X.shape[0]
	remaining_data = X 	# Remaining data to cluster
	remaining_inds = np.arange(N, dtype=np.int64) # Remaining indices of data to cluster (indexes original data X)
	final_clustering = []
	cont = N >= min_cluster_size
	n = 0

	while cont:
		temps, labelings = run_spc(remaining_data, Tmin, Tmax, Ntemps, cycles, Knn, MSTree=MSTree, metric=metric, random_seed=random_seed)
		clustering = collapse_labelings_to_clustering(remaining_data, labelings, cluster_dist_threshold)
		small_clusters = []
		for cluster in clustering:
			if cluster.size >= min_cluster_size:
				final_clustering.append(remaining_inds[cluster])
			else:
				small_clusters.append(cluster)

		n += 1
		cont = (n < n_rounds) and len(small_clusters) > 0

		# More rounds to be performed
		if cont:
			unclustered = np.concatenate(small_clusters) 
			remaining_inds = remaining_inds[unclustered]
			remaining_data = X[remaining_inds]
			cont &= unclustered.size >= min_cluster_size # Don't continue further rounds if there isn't enough remaining data 

	return final_clustering

def collapse_labelings_to_clustering(
		X: npt.NDArray[np.float64], 				# Input data (N_samples, M_features)
		labelings: Labeling, 								# Output of run_spc; (K_levels, N_samples)
		cluster_dist_threshold: float 				# Similarity threshold at which to merge clusters (higher -> finer clustering); should be in same units as data
	) -> Clustering:
	'''
	Construct a cluster tree and collapse tree according to similarity criterion.
	'''
	tree = SPCTree.construct(labelings)
	clustering = collapse_tree(tree, cluster_dist_threshold, X)
	return clustering

def run_spc(
		X: npt.NDArray[np.float64], 	# Input data (N_samples, M_features)
		Tmin: float, 									# Minimum temperature
		Tmax: float, 									# Maximum temperature
		Ntemps: int, 									# Number of temperatures to run, inclusive of the endpoints
		cycles: int, 									# No. cycles to run
		Knn: int, 										# K nearest neighbors to include in neighborhood
		MSTree: bool=True, 						# Whether to include minimum spanning tree edges 
		metric: str='euclidean', 			# Metric space (see scipy.spatial.distance.cdist for options)
		random_seed: Optional[int]=None # Random seed
	) -> Tuple[npt.NDArray[float], Labeling]:
	'''
	Run super-paramagnetic clustering at a range of temperatures and report the cluster labels.
	'''
	assert Ntemps >= 1
	assert Tmax >= Tmin
	if Tmax == Tmin:
		assert Ntemps == 1
		Tstep = 1e-6 # Set minimum Tstep to avoid infinite loop in SPC
	else:
		Tstep = (Tmax - Tmin) / Ntemps
	N = X.shape[0]

	# Handle degenerate cases
	if N == 0:
		return np.linspace(Tmin, Tmax, Ntemps), np.array([[] for _ in range(Ntemps)], dtype=np.int64)
	elif N == 1:
		return np.linspace(Tmin, Tmax, Ntemps), np.array([[0] for _ in range(Ntemps)], dtype=np.int64)
	else:
		# Ensure that Knn <= N (otherwise causes invalid array access in SPC)
		Knn = min(Knn, N)
		dists = cdist(X, X, metric=metric)
		(temps, labelings) = ephys2._cpp.super_paramagnetic_clustering(
			dists,
			Tmin,
			Tmax,
			Tstep,
			cycles,
			Knn,
			MSTree,
			random_seed
		)

		return (temps, labelings)
