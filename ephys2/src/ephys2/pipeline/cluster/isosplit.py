'''
ISO-SPLIT clustering stage
'''

import numpy as np
import numpy.typing as npt

from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.isosplit import *
from .base import *

class IsosplitStage(ClusteringStage):

	@staticmethod
	def name() -> str:
		return 'isosplit'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'n_components': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of principal components in ISO-SPLIT'
			),
			'isocut_threshold': FloatParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'ISO-SPLIT cluster cutting threshold; nominal value 1, lower means more clusters'
			),
			'min_cluster_size': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Minimum cluster size to consider splitting'
			),
			'K_init': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Over-clustering initialization; should be larger than max expected number of units'
			),
			'refine_clusters': BoolParameter(
				units = None,
				description = 'Whether to run the refine_clusters procedure in iso-split'
			),
			'max_iterations_per_pass': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Maximum number of splitting iterations'
			),
			'jitter': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'μV',
				description = 'Standard deviation of white noise added to features to prevent numerical errors'
			),
		}

	def process(self, data: npt.NDArray[np.float32]) -> Labeling:
		'''
		Cluster the data using ISO-SPLIT.
		'''
		return isosplit5_pca_branch(
			data, 
			n_components = self.cfg['n_components'],
			isocut_threshold = self.cfg['isocut_threshold'],
			min_cluster_size = self.cfg['min_cluster_size'],
			K_init = self.cfg['K_init'],
			refine_clusters = self.cfg['refine_clusters'],
			max_iterations_per_pass = self.cfg['max_iterations_per_pass'],
			jitter = self.cfg['jitter'],
			random_seed = 0
		)