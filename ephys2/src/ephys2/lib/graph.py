'''
Graph data structures & algorithms
'''
from typing import Tuple, Any, Set
from dataclasses import dataclass
import scipy.sparse as sp
import numpy as np
import numpy.typing as npt

from ephys2.lib.singletons import rng
from ephys2 import _cpp
from .sparse import *

''' Data structures '''

@dataclass
class EVIncidence(CSRMatrix):
	'''
	A graph represented by an incidence matrix between edges (rows) and vertices (columns).
	'''
	def check_format(self):
		super().check_format()
		# Check that every row has exactly 0 or 2 entries
		if self.indptr.size > 0:
			assert all(x in [0, 2] for x in np.diff(self.indptr)), 'Invalid format'

''' Algorithms '''

def empty_ev_graph() -> EVIncidence:
	'''
	Construct an empty graph.
	'''
	return empty_csr(0, dtype=bool)

def ev_graph_union(ev1: EVIncidence, ev2: EVIncidence) -> EVIncidence:
	'''
	Union of two edge-vertex graphs.
	'''
	# assert ev1.shape[1] == ev2.shape[1], 'Received graphs of different vertex sets'
	return csr_concat((ev1, ev2))

def pairs_to_ev_graph(ps: Iterable[Tuple[Any, Any]], N: int) -> EVIncidence:
	'''
	Convert a sequence of pairs into a edge-vertex incidence matrix.
	'''
	ps = np.array(ps, dtype=np.int64)
	M = ps.shape[0]
	indices = ps.ravel()
	indptr = np.arange(M + 1) * 2
	data = np.full(indices.size, True)
	mat = CSRMatrix(data, indices, indptr, (M, N))
	return mat

def random_ev_graph(n_vertices: int) -> EVIncidence:
	'''
	Generate a random edge-vertex graph with the given vertices.
	'''
	n_edges = rng.integers(0, n_vertices * (n_vertices - 1) // 2)
	return pairs_to_ev_graph(rng.integers(0, n_vertices, size=(n_edges, 2)), n_vertices)

def find_connected_component(node: int, ev: EVIncidence) -> Set[int]:
	'''
	Find the connected component of a node in an edge-vertex graph.
	'''
	return _cpp.find_connected_component(node, ev.tuple())