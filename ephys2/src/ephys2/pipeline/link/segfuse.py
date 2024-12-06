'''
Segmentation fusion-based linking stage
'''

import numpy as np
import numpy.typing as npt
import cvxpy as cp
import scipy.sparse as sp

from ephys2.lib.types import *
from ephys2.lib.cluster import *

try: 
	import gurobipy
except:
	gurobipy = None

class SegfuseStage(ProcessingStage):

	@staticmethod
	def name() -> str:
		return 'segmentation_fusion'

	def type_map(self) -> Dict[type, type]:
		return {LinkCandidates: EVIncidence}

	@staticmethod
	def parameters() -> Parameters:
		return {
			'link_threshold': FloatParameter(
				start = 0,
				stop = 1,
				units = None,
				description = 'Threshold for linking two clusters across distinct blocks; lower produces more links'
			),
			'link_sig_s': FloatParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Sigmoidal scale parameter for link weights'
			),
			'link_sig_k': FloatParameter(
				start = -np.inf,
				stop = np.inf,
				units = None,
				description = 'Sigmoidal offset parameter for link weights; higher means more links'
			),
		}

	def initialize(self):
		self.has_gurobi = cp.GUROBI in cp.installed_solvers()
		if self.has_gurobi:
			assert not (gurobipy is None), 'GUROBI is installed but gurobipy is not. Please check your environment.'
			self.gurobi_env = gurobipy.Env(empty=True)
			self.gurobi_env.setParam('OutputFlag', 0) # Suppress license info being printed to stdout
			self.gurobi_env.setParam('NodefileStart', 0.5) # Start writing to nodefile at 0.5GB memory use
			self.gurobi_env.setParam('Threads', 1) # Use only one thread
			self.gurobi_env.start()

	def process(self, lc: LinkCandidates) -> EVIncidence:
		'''
		Segmentation fusion-based linking step
		'''
		# Get clusters
		block1_clusters = np.unique(lc.block1_labels)
		block2_clusters = np.unique(lc.block2_labels)
		
		# Calculate centroids (ordered by block_i_clusters)
		block1_centroids = np.array([lc.block1_features[lc.block1_labels == C].mean(axis=0) for C in block1_clusters], dtype=np.float32)
		block2_centroids = np.array([lc.block2_features[lc.block2_labels == C].mean(axis=0) for C in block2_clusters], dtype=np.float32)

		# Calculate link weights, stored in the format: (e_11, ..., e_1j, ..., e_i1, ..., e_ij)
		link_format = np.vstack((
			np.repeat(np.arange(block1_clusters.size), block2_clusters.size),
			np.tile(np.arange(block2_clusters.size), block1_clusters.size)
		))
		link_weights = calc_link_weights(block1_centroids, block2_centroids, self.cfg['link_sig_s'], self.cfg['link_sig_k']).ravel()
		
		# Set up ILP
		n_total_links = block1_clusters.size * block2_clusters.size
		link_params = cp.Variable(link_weights.size, boolean=True)
		objective = link_params @ (link_weights - self.cfg['link_threshold'])
		A_data = np.ones(n_total_links)
		A_cols = np.arange(n_total_links)
		A_inbound = sp.coo_matrix((A_data, (link_format[0], A_cols)), shape=(block1_clusters.size, n_total_links)).tocsr()
		b_inbound = np.ones(block1_clusters.size)
		A_outbound = sp.coo_matrix((A_data, (link_format[1], A_cols)), shape=(block2_clusters.size, n_total_links)).tocsr()
		b_outbound = np.ones(block2_clusters.size)
		constraints = [
			A_inbound @ link_params <= b_inbound, # Inbound constraints
			A_outbound @ link_params <= b_outbound # Outbound constraints
		]
		problem = cp.Problem(cp.Maximize(objective), constraints)

		# Solve ILP
		if self.has_gurobi: # Use GUROBI solver if available (faster)
			problem.solve(cp.GUROBI, env=self.gurobi_env) 
		else:
			problem.solve(cp.GLPK_MI)

		# Recover links
		solved_links = link_format[:, link_params.value.astype(bool)]
		n_links = solved_links.shape[1]
		block1_nodes = block1_clusters[solved_links[0]]
		block2_nodes = block2_clusters[solved_links[1]]
		linkage_indices = np.vstack((block1_nodes, block2_nodes)).T.ravel()
		linkage_indptr = np.arange(0, n_links + 1) * 2
		linkage_data = np.full(n_links * 2, True)
		linkage = CSRMatrix(linkage_data, linkage_indices, linkage_indptr, (n_links, lc.label_space))

		return linkage

def calc_link_weights(
		centroids1: npt.NDArray[np.float32], 
		centroids2: npt.NDArray[np.float32],
		link_sig_s: float,
		link_sig_k: float
	) -> npt.NDArray[np.float32]:
	'''
	Calculate pairwise link weights by rescaled distance between centroids.
	'''
	assert len(centroids1.shape) == len(centroids2.shape) == 2
	assert centroids1.shape[1] == centroids2.shape[1]
	M = centroids1.shape[1]
	# First rescale the centroids (not documented in paper, but see FAST source)
	Ka = np.maximum.outer(centroids1.max(axis=1), centroids2.max(axis=1))
	Kb = np.maximum.outer(centroids1.min(axis=1), centroids2.min(axis=1))
	K = Kb - Ka
	# Distance between rescaled centroids
	D = np.sqrt(np.linalg.norm(
		(centroids1[:, np.newaxis, :] - centroids2[np.newaxis, :, :]) / K[:, :, np.newaxis], 
		axis=2
	) / M)
	assert D.shape[0] == centroids1.shape[0]
	assert D.shape[1] == centroids2.shape[0]
	# Scaled distance
	A = np.exp(-(D - link_sig_k) / link_sig_s)
	return A / (1 + A)

