'''
Stage for splitting final data into sessions
'''
import os
import numpy as np
from datetime import datetime, timedelta

from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, logger
from ephys2.lib.h5 import *

class SplitSessionsStage(ProcessingStage):

	@staticmethod
	def name() -> str:
		return 'split_sessions'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'name': StringParameter(
				units = None,
				description = 'Name given to each split session file; will be disambiguated if duplicate paths exist'
			),
		}

	def type_map(self) -> Dict[type, type]:
		return {
			VMultiBatch: VMultiBatch,
			LVMultiBatch: LVMultiBatch,
		}

	def initialize(self):
		self.session_splits = []
		self.serializers = []
		
		if ('session_splits' in global_metadata) and len(global_metadata['session_splits']) > 0:
			self.session_splits = global_metadata['session_splits']
			assert 'session_paths' in global_metadata
			assert len(global_metadata['session_paths']) == len(self.session_splits), 'Number of input paths and time splits inconsistent'
			for i, path in enumerate(global_metadata['session_paths']):
				s = self.make_serializer()
				s.initialize(os.path.join(path, f'session_{i}_{self.cfg["name"]}'))
				self.serializers.append(s)

		self.n_splits = len(self.session_splits)

	def make_serializer(self) -> H5Serializer:
		return {
			VMultiBatch: H5VMultiBatchSerializer,
			LVMultiBatch: H5LVMultiBatchSerializer,
		}[self.input_type()](
			full_check=False,
			rank=self.rank,
			n_workers=self.n_workers
		)

	def process(self, data: VMultiBatch) -> VMultiBatch:
		if self.n_splits > 0:
			# Split data
			subdata = [dict() for _ in range(self.n_splits)]
			for item_id, item in data.items.items():
				assert item.overlap == 0, 'Overlap not allowed in split_sessions'
				for i, end in enumerate(self.session_splits):
					start = 0 if i == 0 else self.session_splits[i-1]
					mask = np.logical_and(item.time >= start, item.time < end)
					assert not (item_id in subdata[i])
					subdata[i][item_id] = item[mask]
			# Write data
			for i, subdatum in enumerate(subdata):
				# Wrap in the proper constructor
				chunk = type(data)(items=subdatum) 
				self.serializers[i].write(chunk)

		return data

	def finalize(self):
		logger.print(f'Splitting sessions at: {self.session_splits}')
		for i in range(self.n_splits):
			# Set global metadata prior to finalizing
			if 'session_splits' in global_metadata:
				del global_metadata['session_splits']
			if 'session_paths' in global_metadata:
				del global_metadata['session_paths']

			# Note - we don't change the timebase when splitting session (i.e. timestamps will be measured w.r.t. the original start time)
			# start_time = self.start_time if i == 0 else (self.start_time + timedelta(seconds=self.session_splits[i-1] / global_metadata['sampling_rate']))
			# global_metadata['start_time'] = start_time.isoformat()

			# Run finalization
			self.serializers[i].serialize()
			self.serializers[i].cleanup()
			logger.print(f'split_sessions wrote file: {self.serializers[i].out_path}')

