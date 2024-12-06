'''
Intrinsic benchmarking metrics (without ground-truth data)
'''
from dataclasses import dataclass
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import h5py

from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.h5 import *
from ephys2.lib.utils import *
from ephys2.lib.transforms import *
from ephys2.lib.singletons import global_metadata, global_state
from ephys2.lib.metrics import *

from .base import *

@dataclass_json
@dataclass
class UnitBenchmark:
	presence_ratio: float
	isi_violation: float
	amp_violation: float
	firing_rate_statistics: SummaryStats
	peak_statistics: SummaryStats
	snr_statistics: SummaryStats
	# nn_isolation_statistics: SummaryStats

@dataclass_json
@dataclass
class ChGroupBenchmark:
	n_blocks: int
	presence_ratio_statistics: SummaryStats
	n_units_statistics: SummaryStats
	units: Dict[int, UnitBenchmark]

@dataclass_json
@dataclass
class IntrinsicBenchmark(Benchmark):
	chgroups: Dict[str, ChGroupBenchmark]
	tag: str = 'IntrinsicBenchmark'


class IntrinsicBenchmarksStage(BenchmarksStage):
	full_check: bool = False
	spatial_offset: float = 10
	random_seed: int = 0

	@staticmethod
	def name() -> str:
		return 'intrinsic'

	def type_map(self) -> Dict[type, type]:
		return {
			LVMultiBatch: LVMultiBatch,
			LLVMultiBatch: LLVMultiBatch,
			SLLVMultiBatch: SLLVMultiBatch,
		}

	@staticmethod
	def parameters() -> Parameters:
		return BenchmarksStage.parameters() | {
			'refractory_period': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'ms',
				description = 'Absolute refractory period for ISI violation calculation'
			),
			'amplitude_cutoff': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'μV',
				description = 'Absolute amplitude below which a spike is considered a false-positive'
			),
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
				description = 'Parameter of symmetric Beta distribution used to weight snippets prior to clustering'
			),
			'n_channels': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of channels in each channel group (e.g. 4 for tetrode)'
			),
			'knn': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Maximum number of nearest-neighbors to use in isolation quality calculation. Higher means lower scores.'
			)
		}

	def initialize(self):
		self.chgroups = dict() # Per-channel group benchmark info
		self.PCA = PCA(n_components=self.cfg['n_components'], svd_solver='randomized', random_state=self.random_seed)
		self.KNN = NearestNeighbors(algorithm='ball_tree')

	def process(self, data: Batch) -> Batch:
		'''
		Compute benchmark data per-block
		'''
		for item_id, item in data.items.items():
			assert item.overlap == 0, 'Do not pass overlapping data to benchmarking stage'

			# Get linked labels, if needed
			labels = item.labels
			# if issubclass(self.input_type(), LLVMultiBatch):
			#	labels = link_labels(labels, item.linkage)

			# Initialize state for local metrics
			if not (item_id in self.chgroups):
				self.chgroups[item_id] = {
					'n_blocks': 0,
					'n_units': [],
					'units': dict(),
				}
			self.chgroups[item_id]['n_blocks'] += 1
			self.chgroups[item_id]['n_units'].append(np.unique(labels).size)

			# Compute per-block metrics
			X = self.feature_transform(item.data)
			assert X.shape[0] == item.data.shape[0]
			if X.shape[0] > 0:
				self.KNN.fit(X)

			# Compute per-unit metrics
			for label in np.unique(labels):
				if not label in self.chgroups[item_id]['units']:
					self.chgroups[item_id]['units'][label] = {
						'n_blocks_present': 0,
						'n_samples': 0,
						'n_isi_violations': 0,
						'n_amp_violations': 0,
						'firing_rate': [],
						'peak': [],
						'snr': [],
						# 'nn_isolation': [],
					}
				unit_time = item.time[labels == label]
				unit_data = item.data[labels == label]
				self.chgroups[item_id]['units'][label]['n_blocks_present'] += 1
				self.chgroups[item_id]['units'][label]['n_samples'] += unit_time.size
				self.chgroups[item_id]['units'][label]['n_isi_violations'] += n_isi_violations(unit_time, global_metadata['sampling_rate'], self.cfg['refractory_period'])
				self.chgroups[item_id]['units'][label]['n_amp_violations'] += n_amp_violations(unit_data, self.cfg['amplitude_cutoff'])
				self.chgroups[item_id]['units'][label]['firing_rate'].append(firing_rate(unit_time, global_metadata['sampling_rate']))
				peak, snr = avg_peak_amplitude_and_snr(unit_data)
				self.chgroups[item_id]['units'][label]['peak'].append(peak)
				self.chgroups[item_id]['units'][label]['snr'].append(snr)
				# self.chgroups[item_id]['units'][label]['nn_isolation'].append(knn_isolation(self.KNN, X[labels == label], label, labels, self.cfg['knn']))

		return data

	def run_benchmark(self) -> IntrinsicBenchmark:
		'''
		Summarize per-block benchmarks into statistics
		'''
		all_chgroups = self.comm.gather(self.chgroups, root=0)

		if self.rank == 0:
			chgroups = dict()
			exc_units = dict()

			for rank_chgroups in all_chgroups:
				for item_id, chgroup in rank_chgroups.items():
					if not (item_id in chgroups):
						chgroups[item_id] = {
							'n_blocks': 0,
							'n_units': [],
							'units': dict(),
						}
						# Read excluded units
						exc_units[item_id] = set()
						with h5py.File(global_state.last_h5, 'r') as file:
							assert file.attrs['tag'] in ['LVMultiBatch', 'LLVMultiBatch', 'SLLVMultiBatch']
							if 'excluded_units' in file[item_id]:
								exc_units[item_id] = set(file[item_id]['excluded_units'][:])

					# Aggregate local benchmarks into global
					chgroups[item_id]['n_blocks'] += chgroup['n_blocks']
					chgroups[item_id]['n_units'].extend(chgroup['n_units'])

					for unit, unit_data in chgroup['units'].items():
						# Do not compute benchmarks for excluded units
						if not (unit in exc_units[item_id]):
							if not (unit in chgroups[item_id]['units']):
								chgroups[item_id]['units'][unit] = {
									'n_blocks_present': 0,
									'n_samples': 0,
									'n_isi_violations': 0,
									'n_amp_violations': 0,
									'firing_rate': [],
									'peak': [],
									'snr': [],
									# 'nn_isolation': [],
								}
							chgroups[item_id]['units'][unit]['n_blocks_present'] += unit_data['n_blocks_present']
							chgroups[item_id]['units'][unit]['n_samples'] += unit_data['n_samples']
							chgroups[item_id]['units'][unit]['n_isi_violations'] += unit_data['n_isi_violations']
							chgroups[item_id]['units'][unit]['n_amp_violations'] += unit_data['n_amp_violations']
							chgroups[item_id]['units'][unit]['firing_rate'].extend(unit_data['firing_rate'])
							chgroups[item_id]['units'][unit]['peak'].extend(unit_data['peak'])
							chgroups[item_id]['units'][unit]['snr'].extend(unit_data['snr'])
							# chgroups[item_id]['units'][unit]['nn_isolation'].extend(unit_data['nn_isolation'])

			return IntrinsicBenchmark(
				method = self.cfg['method_name'],
				dataset = self.cfg['dataset_name'],
				chgroups = {
					item_id: ChGroupBenchmark(
						n_blocks = chgroup['n_blocks'],
						presence_ratio_statistics = SummaryStats.from_array([safe_divide(unit_data['n_blocks_present'], chgroup['n_blocks'], 0) for unit_data in chgroup['units'].values()]),
						n_units_statistics = SummaryStats.from_array(chgroup['n_units']),
						units = {
							int(unit): UnitBenchmark(
								presence_ratio = safe_divide(unit_data['n_blocks_present'], chgroup['n_blocks'], 0),
								isi_violation = safe_divide(unit_data['n_isi_violations'], unit_data['n_samples'], 0),
								amp_violation = safe_divide(unit_data['n_amp_violations'], unit_data['n_samples'], 0),
								firing_rate_statistics = SummaryStats.from_array(unit_data['firing_rate']),
								peak_statistics = SummaryStats.from_array(unit_data['peak']),
								snr_statistics = SummaryStats.from_array(unit_data['snr']),
								# nn_isolation_statistics = SummaryStats.from_array(unit_data['nn_isolation'])
							)
							for unit, unit_data in chgroup['units'].items()
						}
					)
					for item_id, chgroup in chgroups.items()
				}
			)

	def feature_transform(self, X: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		'''
		Apply same feature transform to data used in isosplit_segfuse
		'''
		C = self.cfg['n_channels']
		N = X.shape[0]
		M = X.shape[1] // C
		X = X.reshape((N, C, M)).reshape((N * C, M)) # Reshape to individual waveforms
		wvt = None if self.cfg['wavelet'] == 'none' else self.cfg['wavelet']
		X = beta_truncated_dwt(X, wvt, self.cfg['beta'])
		M = X.shape[1] # Account for possible dimensionality reduction
		X = X.reshape((N, C, M)).reshape((N, C * M)) # Reshape back to concatenated form
		k = min(X.shape)
		if k == 0:
			return X[:, :C * M]
		elif k < self.cfg['n_components']:
			return PCA(n_components=k, svd_solver='randomized', random_state=self.random_seed).fit_transform(X)
		else:
			return self.PCA.fit_transform(X)

