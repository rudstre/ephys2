'''
Loading Ephys2 file formats
'''

import numpy as np
import json
import math
from datetime import datetime

from ephys2.lib.mpi import MPI
from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, global_state
from ephys2.lib.h5.utils import *
from ephys2.lib.loader import *

class LoadStage(InputStage):

	@staticmethod
	def name() -> str:
		return 'load'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'files': ListParameter(
				element = ROFileParameter(units=None, description=''),
				units = None,
				description = 'Files to read data from in sequence'
			),
			'start': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'samples',
				description = 'Starting index in the dataset to read from (inclusive, zero-indexed)'
			),
			'stop': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'samples',
				description = 'Stopping index in the dataset to read until (non-inclusive)'
			),
			'batch_size': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Number of samples to read per batch; determines memory usage and batch size for subsequent stages'
			),
			'batch_overlap': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'samples',
				description = 'Overlap between successively produced batches of data'
			),
		}

	def output_type(self) -> type:
		'''
		Cannot avoid I/O here since it is necessary to know the type of the 
		polymorphic load stage. Thus, load cannot be instantiated except on
		the machine on which it is intended to be run.
		'''
		with open_h5s(self.cfg['files'], 'r') as files:
			tags = [f.attrs['tag'] for f in files]
		assert all(t == tags[0] for t in tags), 'Not all files are of the same type'
		tag = tags[0]
		tag_type = {
			'SBatch': SBatch,
			'VMultiBatch': VMultiBatch,
			'LVMultiBatch': LVMultiBatch,
			'LLVMultiBatch': LLVMultiBatch,
			'SLLVMultiBatch': LLVMultiBatch,
			'LTMultiBatch': LTMultiBatch,
		}[tag]
		logger.debug(f'Load stage producing type {tag_type}')
		return tag_type

	def initialize(self):

		# Read file timestamps from metadata
		with open_h5s(self.cfg['files'], 'r') as files:
			# Record metadata from first file (1st takes precedence)
			global_state.last_h5 = self.cfg['files'][0]
			if 'metadata' in files[0].attrs:
				global_metadata.read_from_string(files[0].attrs['metadata'])
			self.time_offsets = compute_time_offsets(files, global_metadata['sampling_rate'])

		n_files = len(self.cfg['files'])
		if n_files > 0:
			logger.print(f'Received multiple input files; using time offsets: {self.time_offsets}')

		# Initialize loader
		self.loader = {
			SBatch: SBatchLoader,
			VMultiBatch: VMultiBatchLoader,
			LVMultiBatch: LVMultiBatchLoader,
			LLVMultiBatch: LLVMultiBatchLoader,
			LLVMultiBatch: SLLVMultiBatchLoader,
			LTMultiBatch: LTMultiBatchLoader,
		}[self.output_type()](
			self.rank, 
			self.n_workers, 
			self.cfg['start'], 
			self.cfg['stop'], 
			self.cfg['batch_size'],
			self.cfg['batch_overlap'],
		)

	def produce(self) -> Optional[Batch]:
		with open_h5s(self.cfg['files'], 'r') as files:
			return self.loader.load(files, time_offsets=self.time_offsets)	

