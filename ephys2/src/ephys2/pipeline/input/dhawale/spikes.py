'''
Synthetic spike generator (see README.md for details)
'''
from dataclasses import dataclass
import numpy as np
import os
from typing import Optional, Tuple
import pdb

from ephys2.lib.types import *
from ephys2.lib.h5.utils import binary_search_interval
from ephys2.pipeline.input.ground_truth import *

@dataclass
class ChgroupMetadata:
	times_path: ROFilePath
	spikes_path: ROFilePath
	n_samples: int
	gt_time_ref: Any # HDF5 key for ground-truth time data
	gt_label_ref: Any # HDF5 key for ground-truth label data

@dataclass
class DhawaleMetadata(InputMetadata):
	params_path: ROFilePath
	chgroups: Dict[str, ChgroupMetadata]

class DhawaleSpikesStage(GroundTruthInputStage):
	'''
	Reads spikes from data files in the format https://zenodo.org/record/886516#.YiFMg1jML0o
	'''
	sampling_rate = 30000 # Hz
	nsamples = 64 # 64 samples / waveform
	nchans = 4 # 4 channels / snippet
	chgroup_map = { # Mapping between channel group name and actual index in the file
		0: 0,
		1: 1,
		2: 2,
		8: 3,
		9: 4,
		10: 5
	}

	@staticmethod
	def name() -> str:
		return 'spikes'

	def output_type(self) -> type:
		return VMultiBatch
	
	@staticmethod
	def parameters() -> Parameters:
		return GroundTruthInputStage.parameters() | {
			'directory': DirectoryParameter(
				units = None,
				description = 'Directory containing synthetic spike data for all tetrodes'
			),
			'channel_groups': MultiCategoricalParameter(
				categories = [0, 1, 2, 8, 9, 10],
				units = None,
				description = 'Selected channel groups from synthetic recording'
			),
		}

	def make_metadata(self) -> DhawaleMetadata:
		chgroups = dict()
		params_path = f'{self.cfg["directory"]}/dataset_params.mat'

		with h5py.File(params_path, 'r') as pm_file:
			for group in self.cfg['channel_groups']:
				times_path = f'{self.cfg["directory"]}/ChGroup_{group}/SpikeTimes'
				spikes_path = f'{self.cfg["directory"]}/ChGroup_{group}/Spikes'
				n_samples = os.path.getsize(times_path) / 8 # Each time is a 64-bit integer
				assert n_samples == int(n_samples)
				n_samples = int(n_samples)
				chgroups[str(group)] = ChgroupMetadata(
					times_path = times_path,
					spikes_path = spikes_path,
					n_samples = n_samples,
					gt_time_ref = pm_file['sp'][0][self.chgroup_map[group]],
					gt_label_ref = pm_file['sp_u'][0][self.chgroup_map[group]]
				)

		return DhawaleMetadata(
			size = max(md.n_samples for md in chgroups.values()),
			start = self.cfg['start'],
			stop = self.cfg['stop'],
			offset = 0,
			params_path = params_path,
			chgroups = chgroups
		)

	def write_ground_truth(self, md: DhawaleMetadata, path: RWFilePath):
		if self.rank == 0:
			with h5py.File(path, 'w') as gt_file:
				with h5py.File(md.params_path, 'r') as pm_file:
					gt_file.attrs['tag'] = 'LTMultiBatch'
					for group, group_md in md.chgroups.items():
						group_dir = gt_file.create_group(group)
						if md.start < group_md.n_samples:
							[start_time] = np.fromfile(group_md.times_path, dtype=np.uint64, count=1, offset=md.start*8)
							start_idx, _ = binary_search_interval(pm_file[group_md.gt_time_ref], start_time)
							if md.stop < group_md.n_samples:
								[stop_time] = np.fromfile(group_md.times_path, dtype=np.uint64, count=1, offset=md.stop*8)
								_, stop_idx = binary_search_interval(pm_file[group_md.gt_time_ref], stop_time)
							else:
								stop_idx = None
							times = np.squeeze(pm_file[group_md.gt_time_ref][start_idx:stop_idx])
							labels = np.squeeze(pm_file[group_md.gt_label_ref][start_idx:stop_idx])
							group_dir.create_dataset('time', data=times, dtype=np.int64)
							group_dir.create_dataset('labels', data=labels, dtype=np.int64)
						else:
							group_dir.create_dataset('time', data=[], dtype=np.int64)
							group_dir.create_dataset('labels', data=[], dtype=np.int64)

	def load(self, start: int, stop: int) -> VMultiBatch:
		items = dict()
		M = self.nsamples * self.nchans
		for group, group_md in self.metadata.chgroups.items():
			if start < group_md.n_samples:
				stop = min(stop, group_md.n_samples)
				N = stop - start
				vtime = np.fromfile(group_md.times_path, dtype=np.uint64, count=N, offset=start*8).astype(np.int64)
				vdata = np.fromfile(group_md.spikes_path, dtype=np.int16, count=N*M, offset=start*M*2)
				vdata = 0.195 * vdata.astype(np.float32)
				vdata.shape = (N, self.nsamples, self.nchans)
				vdata = vdata.transpose(0, 2, 1).reshape((N, M))
				voverlap = max(0, self.cfg['batch_overlap'] - (self.cfg['batch_size'] - vtime.size)) # Effective overlap
				items[group] = VBatch(
					time = vtime,
					data = vdata,
					overlap = voverlap
				)
			else:
				items[group] = VBatch.empty(M)

		return VMultiBatch(items=items)


