'''
ISO-SPLIT based linking stage
'''

import numpy as np
import numpy.typing as npt
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA

from ephys2.lib.types import *
from ephys2.lib.isosplit import *
from ephys2.pipeline.cluster.isosplit import IsosplitStage as IsosplitClusteringStage

class IsosplitStage(ProcessingStage):

	@staticmethod
	def name() -> str:
		return 'isosplit'

	def type_map(self) -> Dict[type, type]:
		return {LinkCandidates: EVIncidence}

	@staticmethod
	def parameters() -> Parameters:
		return IsosplitClusteringStage.parameters() | {
			'max_cluster_uses': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Maximum number of times a cluster can be used in a link'
			)
		}

	def process(self, lc: LinkCandidates) -> EVIncidence:
		# Get clusters
		block1_clusters = np.unique(lc.block1_labels)
		block2_clusters = np.unique(lc.block2_labels)

		# Calculate centroids (ordered by block_i_clusters)
		block1_centroids = np.array([lc.block1_features[lc.block1_labels == C].mean(axis=0) for C in block1_clusters], dtype=np.float32)
		block2_centroids = np.array([lc.block2_features[lc.block2_labels == C].mean(axis=0) for C in block2_clusters], dtype=np.float32)

		# Calculate pairwise distances
		dists = cdist(block1_centroids, block2_centroids, metric='euclidean').ravel()
		links = np.vstack((
			np.repeat(block1_clusters, block2_clusters.size),
			np.tile(block2_clusters, block1_clusters.size)
		)).T

		# Sort by distance
		links = links[np.argsort(dists)]

		# Form links
		block1_used_nodes = dict()
		block2_used_nodes = dict()
		link_mask = np.full(links.shape[0], False, dtype=bool)
		for i, (C1, C2) in enumerate(links):
			C1_uses = block1_used_nodes.get(C1, 0)
			C2_uses = block2_used_nodes.get(C2, 0)
			if max(C1_uses, C2_uses) < self.cfg['max_cluster_uses']:
				
				# Test if the cluster made of the two sub-clusters would be split
				super_cluster = np.concatenate((
					lc.block1_features[lc.block1_labels == C1],
					lc.block2_features[lc.block2_labels == C2]
				))
				labeling = isosplit5(
					super_cluster,
					n_components = self.cfg['n_components'],
					min_cluster_size = self.cfg['min_cluster_size'],
					K_init = self.cfg['K_init'],
					refine_clusters = self.cfg['refine_clusters'],
					max_iterations_per_pass = self.cfg['max_iterations_per_pass'],
					random_seed = 0,
					jitter = self.cfg['jitter']
				)

				# Add the link if not
				if np.unique(labeling).size == 1:
					link_mask[i] = True
					block1_used_nodes[C1] = C1_uses + 1
					block2_used_nodes[C2] = C2_uses + 1

		# Form incidence matrix
		selected_links = links[link_mask]
		n_links = selected_links.shape[0]
		linkage_indices = selected_links.ravel()
		linkage_indptr = np.arange(0, n_links * 2 + 1, 2)
		linkage_data = np.full(n_links * 2, True)
		linkage = CSRMatrix(linkage_data, linkage_indices, linkage_indptr, (n_links, lc.label_space))

		return linkage