'''
Base classes for benchmarking stages
'''
from typing import Any, Tuple
import numpy as np
import random
from abc import ABC, abstractmethod
import pdb

from ephys2.lib.mpi import MPI
from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata
from ephys2.pipeline.input.ground_truth import *
from .utils import *

class SyntheticSpikesStage(GroundTruthInputStage):
	'''
	Simulates spikes in batches, exploiting the memoryless property of the Poisson process.
	'''

	@staticmethod
	def name() -> str:
		return 'spikes'

	def output_type(self) -> type:
		return VMultiBatch

	@staticmethod
	def parameters() -> Parameters:
		return GroundTruthInputStage.parameters() | {
			'n_samples': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Number of spikes to produce for each tetrode',
			),
			'n_tetrodes': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of tetrodes of data to generate'
			),
			'n_units_per_tetrode': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Number of synthetic neurons per tetrode'
			),
			'min_firing_rate': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'Hz',
				description = 'Minimum of the firing rate distribution, sampled uniformly'
			),
			'max_firing_rate': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'Hz',
				description = 'Maximum of the firing rate distribution, sampled uniformly'
			),
			'refractory_period': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'ms',
				description = 'Absolute refractory period of synthetic neurons'
			),
			'sampling_rate': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'Hz',
				description = 'Sampling rate of the synthetic recording'
			),
			'seed': IntParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Random seed used to synchronize random state across processes and reproduce results'
			),
		}

	def initialize(self):
		assert self.cfg['n_samples'] < np.inf, 'Cannot generate an infinite number of synthetic spikes.'
		super().initialize()
		global_metadata['sampling_rate'] = self.cfg['sampling_rate']

	@abstractmethod
	def get_num_templates(self) -> int:
		'''
		Get the number of templates available in the library.
		'''
		pass

	@abstractmethod
	def get_templates(self, idxs: npt.NDArray[np.int64]) -> npt.NDArray[np.float32]:		
		'''
		Select the spike templates from a library.
		'''
		pass

	@abstractmethod
	def postprocess(self, unit_ids: npt.NDArray[np.int64], wvs: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		'''
		Do any postprocessing of the units for a particular tetrode (should be vectorized).
		'''
		pass

	def make_metadata(self) -> InputMetadata:
		NT = self.get_num_templates()
		K, M = self.cfg['n_units_per_tetrode'], self.cfg['n_tetrodes']
		assert self.cfg['refractory_period'] <= 1000 / self.cfg['max_firing_rate'], 'Cannot have a refractory period greater than the inverse max firing rate'
		assert NT >= M * K, 'Not enough templates available.'

		''' Randomization: must be synchronized across processes. Do not use `rng` in rank-dependent branches. '''
		self.rng = np.random.default_rng(self.cfg['seed'])
		idxs = self.rng.choice(NT, size=M * K, replace=False).astype(np.int64)
		rates = self.rng.uniform(self.cfg['min_firing_rate'], self.cfg['max_firing_rate'], size=M * K)

		self.tetrodes = dict()
		for i in range(M):
			self.tetrodes[i] = {
				'units': self.get_templates(idxs[i * K:(i + 1)*K]),
				'rates': rates[i * K:(i + 1)*K],
				't_offset': 0, 
				'time': None,
				'labels': None,
			}

		self.batch_ctr = self.rank

		return InputMetadata(
			size = self.cfg['n_samples'],
			start = 0,
			stop = self.cfg['n_samples'],
			offset = 0,
		)

	def write_ground_truth(self, md: InputMetadata, path: RWFilePath):
		# Create h5py file with correct size
		items = [str(i) for i in range(self.cfg['n_tetrodes'])]

		if self.rank == 0:
			with h5py.File(self.cfg['ground_truth_output'], 'w') as gt_file:
				gt_file.attrs['tag'] = 'LTMultiBatch'
				for item in items:
					item_dir = gt_file.create_group(item)
					item_dir.create_dataset('time', (md.effective_size,), dtype=np.int64)
					item_dir.create_dataset('labels', (md.effective_size,), dtype=np.int64)

		# Wait for file to be create
		self.comm.Barrier()

		# Write data in parallel
		current_sample = md.start + self.rank * self.cfg['batch_size']
		with h5py.File(self.cfg['ground_truth_output'], 'a', driver='mpio', comm=self.comm) as gt_file:
			if current_sample < md.stop:
				while current_sample < md.stop:
					next_stop = min(current_sample + self.cfg['batch_size'], md.stop)
					data = self.load_ground_truth(current_sample, next_stop)
					for item_id, item in data.items.items():
						gt_file[item_id]['time'][current_sample:next_stop] = item.time
						gt_file[item_id]['labels'][current_sample:next_stop] = item.labels
					current_sample += self.n_workers * self.cfg['batch_size'] # Advance to next assigned block 
			else:
				# Dummy "writes" from non-participating ranks necessary to close file
				for item_id in gt_file.keys():
					assert gt_file[item_id]['time'].shape == gt_file[item_id]['labels'].shape

	def load_ground_truth(self, start: int, stop: int) -> LTMultiBatch:
		self.advance_time()
		items = dict()
		N = stop - start
		for i in self.tetrodes:
			# Poisson times of all 
			times, labels = self.tetrodes[i]['time'], self.tetrodes[i]['labels']
			items[str(i)] = LTBatch(
				time = times[:N],
				labels = labels[:N],
				overlap = 0
			)
		self.batch_ctr += self.n_workers
		return LTMultiBatch(items=items)

	def load(self, start: int, stop: int) -> VMultiBatch:
		'''
		In the synthetic spike generator, ground-truth and input are in 1-1 correspondence.
		'''
		items = dict()
		with h5py.File(self.cfg['ground_truth_output'], 'r') as gt_file:
			for i in self.tetrodes:
				# Poisson times of all 
				times = gt_file[str(i)]['time'][start:stop]
				labels = gt_file[str(i)]['labels'][start:stop]
				# Select units from labels
				spikes = self.postprocess(labels, self.tetrodes[i]['units'][labels])
				items[str(i)] = VBatch(
					time = times,
					data = spikes,
					overlap = 0
				)
		return VMultiBatch(items=items)

	def advance_time(self):
		'''
		Produce event times, advancing time for RNG synchronization in multiprocess mode
		'''
		n = (self.rank + 1) if self.batch_ctr == self.rank else self.n_workers

		for _ in range(n):
			for i in self.tetrodes:
				times, labels = poisson_refr_superposition(
					self.rng,
					self.tetrodes[i]['rates'],
					self.cfg['refractory_period'],
					self.cfg['sampling_rate'],
					self.cfg['batch_size'] 
				)
				times += self.tetrodes[i]['t_offset']
				self.tetrodes[i]['t_offset'] = times[-1] if times.size > 0 else 0
				self.tetrodes[i]['time'] = times
				self.tetrodes[i]['labels'] = labels

