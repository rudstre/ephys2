'''
Types & algorithms for clustering
'''
from typing import Dict, List, Callable, Any, Union, NewType, Optional, Tuple, Set, FrozenSet
import numpy as np
import numpy.typing as npt
import random

from .graph import *
from ephys2 import _cpp

''' Data structures '''

'''
A labeling of data is a surjective map onto a contiguous subset of the natural numbers.
'''
Labeling = npt.NDArray[np.int64] 			
'''
A clustering of data is a grouping of its indices. May not contain all indices, in which case per-datum label is implied.
'''
Cluster = npt.NDArray[np.int64]
Clustering = List[Cluster]
'''
A mapping between two different label sets
'''
LabelMap = Dict[np.int64, np.int64]

@dataclass
class LinkCandidates:
	block1_labels: Labeling
	block2_labels: Labeling
	block1_features: npt.NDArray[np.float32]
	block2_features: npt.NDArray[np.float32]
	label_space: np.int64

''' Algorithms '''

def clustering_to_labeling(clustering: Clustering, N: int) -> Tuple[Labeling, int]:
	'''
	Convert a clustering to a labeling. 
	Any un-clustered data are labeled by additional numbers.
	Takes a set of clusters and the size of the data space, and returns the labeling and size of the cluster space.
	''' 
	labeling = np.full(N, -1, dtype=int)
	nclus = 0
	for cluster in clustering:
		labeling[cluster] = nclus
		nclus += 1
	for i, v in enumerate(labeling):
		if v == -1: # Unclustered, make a singleton cluster
			labeling[i] = nclus
			nclus += 1
	return labeling, nclus

def labeling_to_clustering(labeling: Labeling, indices: Optional[npt.NDArray]=None) -> Clustering:
	'''
	Convert a labeling to a clustering. 
	''' 
	labels = np.unique(labeling)
	clustering = []
	for lb in labels:
		cluster = np.nonzero(labeling == lb)[0] if indices is None else indices[labeling == lb]
		clustering.append(cluster)
	return clustering

def eq_clustering(c1: Clustering, c2: Clustering) -> bool:
	return all(np.allclose(c1[i], c2[i]) for i in range(len(c1)))

def link_labels(labels: Labeling, linkage: EVIncidence) -> Labeling:
	'''
	Link labels using an edge-vertex graph, returning the minimum label for each connected component.
	'''
	result = np.zeros_like(labels, dtype=np.int64)
	_cpp.link_labels(labels, result, linkage.tuple())
	return result

def link_labels_py(labels: Labeling, linkage: EVIncidence) -> Labeling:
	'''
	Link labels using an edge-vertex graph, returning the minimum label for each connected component.
	(Python version, for testing purposes.)
	'''
	result = np.zeros_like(labels, dtype=np.int64)
	lookup = dict()
	for i, label in enumerate(labels):
		if label in lookup:
			result[i] = lookup[label]
		else:
			# Compute and store connected component using BFS
			seen = set()
			cc = []
			queue = [label]
			while len(queue) > 0:
				v = queue.pop()
				if v in seen:
					continue
				seen.add(v)
				cc.append(v)
				# Find neighbors
				row_indices, col_data = csr_getcol(linkage, v)
				for row_idx, col_val in zip(row_indices, col_data):
					if col_val: 
						# If the edge exists, add neighbors to the queue
						neighbors = linkage.get_row_indices(row_idx)
						queue.extend(neighbors)
			cc_label = min(cc)
			for v in cc:
				lookup[v] = cc_label
			result[i] = cc_label
	return result

def random_labeling(N: int, K: int) -> Labeling:
	'''
	Generate an N-length random event stream containing exactly 0...K-1 as its unique elements.
	'''
	assert N >= K, 'Cannot sample fewer than K unique events'
	result = [0] * N
	# Choose K indices
	nCk = random.sample(range(N), K)
	# Set indices to unique events
	kP = random.sample(range(K), K)
	for i, j in enumerate(nCk):
		result[j] = kP[i]
	# Set remaining indices to any events
	for j in range(N):
		if not (j in nCk):
			result[j] = random.randrange(K)
	return np.array(result, dtype=np.int64)

def add_links(linkage: EVIncidence, nodes: List[int]) -> EVIncidence:
	'''
	Add links to an edge-vertex graph.
	By convention, we add edges in vertex-sorted order.
	'''
	if len(nodes) >= 2:
		nodes = np.array(nodes)
		nodes.sort()
		links = np.vstack((nodes[:-1], nodes[1:])).T.ravel()
		nlinks = nodes.size - 1
		data = np.append(linkage.data, np.full(links.size, True)) # Add nonzeros
		indices = np.append(linkage.indices, links) # Add nodes
		indptr = np.append(linkage.indptr, linkage.indptr[-1] + np.cumsum(np.full(nlinks, 2))) # Add indptr
		shape = (linkage.shape[0] + nlinks, linkage.shape[1])
		linkage = CSRMatrix(data, indices, indptr, shape)
		# linkage.check_format()
	return linkage