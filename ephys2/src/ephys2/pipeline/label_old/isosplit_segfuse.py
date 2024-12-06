'''
Old FAST-style segmentation fusion step using ISO-SPLIT as the clustering algorithm
'''
import numpy as np
import numpy.typing as npt
import cvxpy as cp
from dataclasses import dataclass
import scipy.stats as stats

from .base import *
from .spc_segfuse import *

from ephys2.lib.types import *
from ephys2.lib.isosplit import *
from ephys2.lib.transforms import *
from ephys2.docs import get_path

class IsosplitSegFuseStage(LabelingStage):

	@staticmethod
	def name() -> str:
		return 'isosplit_segfuse'

	@staticmethod
	def parameters() -> Parameters:
		return LabelingStage.parameters() | {
			'n_components': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of principal components in feature extraction'
			),
			'wavelet': CategoricalParameter(
				categories = ['none'] + pywt.wavelist(kind='discrete'),
				units = None,
				description = 'Choice of wavelet used in discrete wavelet transform feature extraction; set to none or one of http://wavelets.pybytes.com/'
			),
			'beta': FloatParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Parameter of symmetric Beta distribution used to weight spike waveforms prior to clustering'
			),
			'n_channels': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of channels in each channel group (e.g. 4 for tetrode)'
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

	def feature_transform(self, X: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		'''
		Apply the feature transform prior to clustering.
		'''
		# Reshape into per-channel waveforms & apply feature transform
		C = self.cfg['n_channels']
		M = X.shape[1] // C
		N = X.shape[0]
		Y = X.reshape((N, C, M)).reshape((N * C, M)) # Reshape to individual waveforms
		wvt = None if self.cfg['wavelet'] == 'none' else self.cfg['wavelet']
		Y = beta_truncated_dwt(Y, wvt, self.cfg['beta'])
		M = Y.shape[1] # Account for possible dimensionality reduction
		Y = Y.reshape((N, C, M)).reshape((N, C * M)) # Reshape back to concatenated form
		return Y

	def run_clustering(self, X: npt.NDArray[np.float32]) -> Labeling:
		'''
		Cluster the data using ISO-SPLIT.
		'''
		return isosplit5_pca_branch(
			X, 
			n_components = self.cfg['n_components'],
			isocut_threshold = self.cfg['isocut_threshold'],
			min_cluster_size = self.cfg['min_cluster_size'],
			K_init = self.cfg['K_init'],
			refine_clusters = self.cfg['refine_clusters'],
			max_iterations_per_pass = self.cfg['max_iterations_per_pass'],
			jitter = self.cfg['jitter'],
			random_seed = 0
		)

	@classmethod 
	def description(cls: type) -> str:
		'''
		Description of stage written in rST
		'''
		with open(get_path('isosplit_segfuse.rst'), 'r') as file:
			return file.read()
