'''
Base checkpointing stage

TODO: move away from POSIX-specific filepaths.
TODO: exception safety
TODO: handle case where worker has done no work
'''
import numpy as np
from abc import abstractmethod
import os
import warnings
import h5py
import shutil
import glob

from ephys2.lib.mpi import MPI
from ephys2.lib.types import *
from ephys2.lib.utils import ext_mul
from ephys2.lib.singletons import logger, global_state
from ephys2.lib.loader import *
from ephys2.lib.h5 import *

class CheckpointStage(ProcessingStage, ProducerStage):
	'''
	Enforces a barrier-like serialization mechanism
	'''
	@staticmethod
	def name() -> str:
		return 'checkpoint'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'batch_size': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'samples',
				description = 'Size of data batches which will be passed to subsequent stages'
			),
			'batch_overlap': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'samples',
				description = 'Overlap between data batches fed to subsequent stages'
			),
			'file': RWFileParameter(
				units = None,
				description = 'File path where data is written in HDF5 format'
			),
		}

	def type_map(self) -> Dict[type, type]:
		'''
		Checkpointing transparently serializes and re-batches a data stream.
		'''
		return {
			SBatch: SBatch,
			VMultiBatch: VMultiBatch,
			LVMultiBatch: LVMultiBatch,
			LLVMultiBatch: LLVMultiBatch,
			SLLVMultiBatch: LLVMultiBatch, # SLLVBatch can only be read into LLVBatch
			LTMultiBatch: LTMultiBatch,
		}

	def initialize(self):

		# Warn if the batch size is infinite
		if self.cfg['batch_size'] == np.inf:
			logger.warn(f'Using infinite batch size, this will result in single-threaded performance and will load all results from {self.cfg["name"]} into memory.')

		# Serializer 
		self.serializer = {
			SBatch: H5SBatchSerializer,
			VMultiBatch: H5VMultiBatchSerializer,
			LVMultiBatch: H5LVMultiBatchSerializer,
			LLVMultiBatch: H5LLVMultiBatchSerializer,
			SLLVMultiBatch: H5SLLVMultiBatchSerializer,
			LTMultiBatch: H5LTMultiBatchSerializer,
		}[self._input_type](
			full_check=global_state.debug, 
			rank=self.rank, 
			n_workers=self.n_workers
		)
		self.serializer.initialize(self.cfg['file'])

		# Loader
		self.loader = {
			SBatch: SBatchLoader,
			VMultiBatch: VMultiBatchLoader,
			LVMultiBatch: LVMultiBatchLoader,
			LLVMultiBatch: LLVMultiBatchLoader,
			SLLVMultiBatch: SLLVMultiBatchLoader,
			LTMultiBatch: LTMultiBatchLoader,
		}[self._input_type](
			self.rank, 
			self.n_workers, 
			0, 
			np.inf, 
			self.cfg['batch_size'],
			self.cfg['batch_overlap'],
		)

	def process(self, data: Batch):
		'''
		Write chunks to separate file-per-process
		'''
		self.serializer.write(data)

	def serialize(self):
		'''
		Workers serialize the results from the temporary files using Parallel HDF5. Makes two calls to MPI Barrier to isolate writes and subsequent reads.
		'''
		self.serializer.serialize()
		self.serializer.cleanup()

	def produce(self) -> Optional[Batch]:
		'''
		Once the results have been serialized, this stage is used as the input stream.
		'''
		with h5py.File(self.cfg['file'], 'r') as savefile:
			return self.loader.load(savefile)	


