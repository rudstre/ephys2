'''
Old FAST-style segmentation fusion step for chaining clusters
'''

import numpy as np
import cvxpy as cp
import time

from .base import *

from ephys2.lib.types import *
from ephys2.lib.singletons import logger
from ephys2.lib.spc import run_spc, SPCTree

class SPCSegFuseStage(LabelingStage):

	@staticmethod
	def name() -> str:
		return 'spc_segfuse'

	@staticmethod
	def parameters() -> Parameters:
		return LabelingStage.parameters() | {
			't_min': FloatParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Minimum of temperature range for super-paramagnetic clustering'
			),
			't_max': FloatParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Maximum of temperature range for super-paramagnetic clustering'
			),
			'n_temps': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of temperatures at which to run super-paramagnetic clustering'
			),
			'knn': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Maximum number of nearest-neighbors to use in SPC knn algorithm'
			),
			'cycles': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of Swensen-Wang sweeps in SPC'
			),
			'metric': CategoricalParameter(
				categories = ['euclidean', 'cityblock', 'cosine', 'correlation', 'hamming', 'chebyshev', 'mahalanobis'],
				units = None,
				description = 'Metric to use in distance calculations for SPC'
			),
		}

	def label_and_link(self, 
			block1: npt.NDArray[np.float32], 
			block2: Optional[npt.NDArray[np.float32]], 
			labels_start: int,
			label_space: int
		) -> Tuple[Labeling, EVIncidence]:
		'''
		Label and link data across two blocks.
		- labels_start provides the start of the label space
		- block_size provides the size of the label block
		- label_space provides the size of the entire label space
		If the second data block is not provided, this method just performs clustering.

		This method overrides the original due to the SPC tree algorithm.
		'''
		empty_graph = empty_csr(label_space, dtype=bool)

		# Empty case
		if block1.size == 0:
			return np.zeros(0, dtype=np.int64), empty_graph

		node_clusters: List[Cluster] = []																# Clusters corresponding to each node
		link_ids: List[Tuple[int, int]] = []														# Index : (node id, node id) mapping
		node_weights: List[float] = []																	# Vector of all node weights
		link_weights: List[float] = []																	# Vector of all link weights
		n_nodes = 0																											# Number of total node parameters
		n_links = 0																											# Number of total link parameters
		last_tree = None 																								# Last tree 
		last_centroids = None

		# Constraint matrix coordinates
		inbound_constr_rows = []
		inbound_constr_cols = []
		outbound_constr_rows = []
		outbound_constr_cols = []
		cluster_constr_rows = []
		cluster_constr_cols = []
		n_total_paths = 0

		blocks = [block1] if block2 is None else [block1, block2]
		K = len(blocks)
		N = sum(block.shape[0] for block in blocks)
		for k, bX in enumerate(blocks):
			_, labelings = run_spc(
				bX, 
				self.cfg['t_min'], 
				self.cfg['t_max'], 
				self.cfg['n_temps'],
				self.cfg['cycles'],
				self.cfg['knn'],
				metric=self.cfg['metric'],
				random_seed=0
			)
			tree = SPCTree.construct(labelings)
			logger.debug(f'Tree: {len(tree)}')

			# Visit nodes
			for node in tree.dfs():
				# Set node ID
				node.id = n_nodes
				# Offset cluster indices by current block
				node_clusters.append(node.cluster + k * B)
				# Calculate weight
				node_weights.append(calc_node_weight(node))
				n_nodes += 1

			# Get centroids
			centroids = np.array([
				bX[node.cluster].mean(axis=0) for node in tree.dfs()
			], dtype=np.float32)

			# Visit edges, if there are any
			if not (last_tree is None):

				link_weights.append(
					self.calc_link_weights(last_centroids, centroids).ravel()
				)

				# Visit links
				for node1 in last_tree.dfs():
					for node2 in tree.dfs():
						link_ids.append((node1.id, node2.id))

						# Track link constraints
						inbound_constr_rows.append(node1.id)
						inbound_constr_cols.append(n_links)
						outbound_constr_rows.append(node2.id)
						outbound_constr_cols.append(n_links)

						n_links += 1

			# Add nonoverlapping cluster constraints
			for path in tree.dfs_paths():
				# Only count non-singleton paths
				if len(path) > 1: 
					path_ids = [node.id for node in path]
					cluster_constr_cols.extend(path_ids)
					cluster_constr_rows.extend([n_total_paths] * len(path_ids))
					n_total_paths += 1

			# Add the tree for this window
			last_tree = tree
			last_centroids = centroids

		# Construct ILP
		node_weights = np.array(node_weights, dtype=np.float32)
		node_params = cp.Variable(node_weights.size, boolean=True)
		objective = node_params @ node_weights
		constraints = []

		# If there exist any links to be found:
		# 1. 	Add link objective
		# 2. 	Encode constraints in sparse matrices
		# 		Add inbound & outbound link constraints
		if K > 1: 
			link_weights = np.concatenate(link_weights)
			link_params = cp.Variable(link_weights.size, boolean=True)
			objective += link_params @ (link_weights - self.cfg['link_threshold'])

			A_values = np.ones(n_links).astype(np.int32)
			A_shape = (n_nodes, n_links)
			A_inbound = sp.coo_matrix((A_values, (inbound_constr_rows, inbound_constr_cols)), shape=A_shape).tocsr()
			A_outbound = sp.coo_matrix((A_values, (outbound_constr_rows, outbound_constr_cols)), shape=A_shape).tocsr()

			constraints.append(A_inbound @ link_params <= node_params)
			constraints.append(A_outbound @ link_params <= node_params)

		# Add nonoverlapping cluster constraints
		A_values = np.ones(len(cluster_constr_rows)).astype(np.int32)
		A_shape = (n_total_paths, n_nodes)
		A_cluster = sp.coo_matrix((A_values, (cluster_constr_rows, cluster_constr_cols)), shape=A_shape).tocsr()

		constraints.append(A_cluster @ node_params <= np.ones(n_total_paths))

		# Solve ILP
		problem = cp.Problem(cp.Maximize(objective), constraints)
		logger.debug('Solving ILP...')
		tsol_start = time.time()
		if self.has_gurobi: # Use GUROBI solver if available (faster)
			problem.solve(cp.GUROBI, env=self.gurobi_env) 
		else:
			problem.solve(cp.GLPK_MI)
		tsol_finish = time.time()
		logger.debug('ILP solved in ' + '{0:0.1f} seconds'.format(tsol_finish - tsol_start))

		# Recover clustering 
		clustering = []
		node_clus_map = dict() # Mapping from node ID to cluster ID
		N_clus = 0
		for k, v in enumerate(node_params.value):
			if v == 1:
				clustering.append(node_clusters[k])
				node_clus_map[k] = N_clus
				N_clus += 1
		labeling, Ks = clustering_to_labeling(clustering, N)
		assert N_clus == Ks

		# Recover links
		Nlinks = 0
		rows, cols = [], []
		if K > 1: # There exist any links to be found
			for k, v in enumerate(link_params.value):
				if v == 1:
					id1, id2 = link_ids[k]
					clus1, clus2 = node_clus_map[id1], node_clus_map[id2]
					cols.append(clus1 + labels_start)
					cols.append(clus2 + labels_start)
					rows.append(Nlinks)
					rows.append(Nlinks)
					Nlinks += 1
		linkage = CSRMatrix.from_sp(sp.coo_matrix(([True] * len(rows), (rows, cols)), shape=(Nlinks, label_space)).tocsr())

		# TODO: postprocessing - link unclustered data

		return labeling, linkage

	def feature_transform(self, X: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		'''
		label_and_link is overridden, this method is no-op
		'''
		pass

	def run_clustering(self, X: npt.NDArray[np.float32]) -> Labeling:
		'''
		label_and_link is overridden, this method is no-op
		'''
		pass

def calc_node_weight(node: SPCTree) -> float:
	'''
	Calculate a node's weight using BFS.
	'''
	N_0 = node.cluster.size
	assert N_0 > 0, 'Got an empty cluster.' # Prevent division-by-zero errors
	N_a = 0
	current_node = node
	while True:
		if current_node.is_leaf():
			break
		else:
			largest_child = None
			largest_size = 0
			for c in current_node.children:
				if c.cluster.size > largest_size:
					largest_child = c
					largest_size = c.cluster.size
			N_a += largest_size
			current_node = largest_child

	return N_0 / (N_0 + N_a)