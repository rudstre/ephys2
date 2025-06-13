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
import math
import time
from typing import Union, Dict
import json

from ephys2.lib.mpi import MPI
from ephys2.lib.types import *
from ephys2.lib.utils import ext_mul
from ephys2.lib.singletons import logger, global_state
from ephys2.lib.loader import *
from ephys2.lib.h5 import *
from ephys2.lib.distribution import WorkerDistribution

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
			
		# Validate batch_size and batch_overlap
		if self.cfg['batch_overlap'] >= self.cfg['batch_size']:
			raise ValueError(f"Batch overlap ({self.cfg['batch_overlap']}) must be less than batch size ({self.cfg['batch_size']})")

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
		
		# Initialize total data size tracking
		self.total_data_size = 0
		self.has_written = False
		self.checked_worker_distribution = False
		self.checked_data_file = None  # Track which file we've already checked
		
	def get_batch_size(self, data: Batch) -> Union[int, Dict[str, int]]:
		"""
		Get the size of a batch object, handling both regular Batch objects with a size property
		and MultiBatch objects that have items.
		
		Returns either an integer (for simple Batch objects) or a dictionary mapping
		channel group IDs to their respective sizes (for MultiBatch objects).
		"""
		if hasattr(data, 'size'):
			return data.size
		elif hasattr(data, 'items'):
			# For MultiBatch objects, return both the sum and individual sizes
			sizes_by_item = {item_id: item.size for item_id, item in data.items.items()}
			return sizes_by_item
		else:
			# Fallback for unknown batch types
			logger.warn(f"Unknown batch type {type(data)}, cannot determine size")
			return 0

	def process(self, data: Batch):
		'''
		Write chunks to separate file-per-process
		'''
		# Track that this worker got data
		self.has_written = True
		
		# Check worker distribution after the first batch
		if not self.checked_worker_distribution:
			self.check_all_workers_got_data()
			self.checked_worker_distribution = True
			
		# Track the total data size
		batch_size = self.get_batch_size(data)
		
		# If it's a dictionary (MultiBatch), aggregate the sizes properly
		if isinstance(batch_size, dict):
			# Initialize dictionary storage if not already done
			if not hasattr(self, 'size_by_channel_group'):
				self.size_by_channel_group = {}
				
			# Add sizes for each channel group
			for item_id, size in batch_size.items():
				if item_id in self.size_by_channel_group:
					self.size_by_channel_group[item_id] += size
				else:
					self.size_by_channel_group[item_id] = size
					
			# Also track total size (sum of all items)
			self.total_data_size += sum(batch_size.values())
		else:
			# Simple integer size
			self.total_data_size += batch_size
			
		# Write the data
		self.serializer.write(data)
	
	def check_all_workers_got_data(self):
		"""
		Check if all workers received data during processing
		"""
		# Gather whether each worker received data
		all_have_data = self.comm.gather(self.has_written, root=0)
		all_sizes = self.comm.gather(self.total_data_size, root=0)
		
		if self.rank == 0:
			# Get parameters from global state for the loader that's feeding data into this checkpoint
			from ephys2.lib.singletons import global_state
			
			# Use global state to get info about the loader producing data for this checkpoint
			if hasattr(global_state, 'load_batch_size') and hasattr(global_state, 'load_overlap'):
				upstream_batch_size = global_state.load_batch_size
				upstream_batch_overlap = global_state.load_overlap
			else:
				# Fallback to the parameters from the loader in this checkpoint
				upstream_batch_size = self.loader.batch_size
				upstream_batch_overlap = self.loader.batch_overlap
			
			# Estimate total size from the workers that did get data
			estimated_total_size = sum(all_sizes)
			
			# Use the centralized WorkerDistribution validation
			error_msg = WorkerDistribution.validate_empirical(
				all_have_data, estimated_total_size, upstream_batch_size, 
				upstream_batch_overlap, self.n_workers)
				
			if error_msg:
				raise AssertionError(error_msg)
		
		self.comm.Barrier()

	def serialize(self):
		'''
		Workers serialize the results from the temporary files using Parallel HDF5. Makes two calls to MPI Barrier to isolate writes and subsequent reads.
		'''	
		# Before serializing, make sure temp files exist for all workers who have written data
		all_has_written = self.comm.gather(self.has_written, root=0)
		all_sizes = self.comm.gather(self.total_data_size, root=0)
		
		# Also gather channel group sizes if available
		has_channel_groups = hasattr(self, 'size_by_channel_group')
		all_has_channel_groups = self.comm.gather(has_channel_groups, root=0)
		
		if has_channel_groups:
			channel_group_sizes = self.comm.gather(self.size_by_channel_group, root=0)
		else:
			channel_group_sizes = self.comm.gather({}, root=0)
		
		if self.rank == 0:
			# Check if temp files exist for workers that reported writing data
			missing_files = []
			for i, has_written in enumerate(all_has_written):
				if has_written:
					tmp_path = self.serializer.get_worker_path(i)
					if not os.path.exists(tmp_path):
						missing_files.append((i, tmp_path))
			
			if missing_files:
				error_msg = f"Missing temporary files for workers that reported writing data:\n"
				for worker, path in missing_files:
					error_msg += f"  Worker {worker}: {path}\n"
				raise RuntimeError(error_msg)
			
			# Aggregate total size (sum of all items)
			total_size = sum(all_sizes)
			logger.debug(f"Serializing data: total_size={total_size}, workers_with_data={sum(1 for x in all_has_written if x)}/{self.n_workers}")
			
			# Aggregate channel group sizes
			aggregated_channel_group_sizes = {}
			for worker_sizes in channel_group_sizes:
				for group_id, size in worker_sizes.items():
					if group_id in aggregated_channel_group_sizes:
						aggregated_channel_group_sizes[group_id] += size
					else:
						aggregated_channel_group_sizes[group_id] = size
			
			# Save both total size and channel group sizes
			self.total_size_to_save = total_size
			self.channel_group_sizes_to_save = aggregated_channel_group_sizes
		
		# Wait for file check to complete
		self.comm.Barrier()
		
		try:
			logger.debug(f"Worker {self.rank}: Starting serialization")
			self.serializer.serialize()
			
			# Save the total data size as an attribute in the file
			if self.rank == 0:
				try:
					with h5py.File(self.cfg['file'], 'a') as h5file:
						h5file.attrs['total_size'] = self.total_size_to_save
						
						# Also save per-channel group sizes if available
						if hasattr(self, 'channel_group_sizes_to_save') and self.channel_group_sizes_to_save:
							h5file.attrs['channel_group_sizes'] = json.dumps(self.channel_group_sizes_to_save)
						
						h5file.attrs['batch_size'] = self.cfg['batch_size'] 
						h5file.attrs['batch_overlap'] = self.cfg['batch_overlap']
						logger.debug(f"Saved metadata: total_size={self.total_size_to_save}")
				except Exception as e:
					logger.warn(f"Error saving total_size metadata: {str(e)}")
			
			logger.debug(f"Worker {self.rank}: Serialization complete")
			
			# Ensure all processes have finished writing before any start reading
			self.comm.Barrier()
			
			# Add a small delay to ensure file handles are fully released
			time.sleep(0.1)
		except Exception as e:
			logger.error(f"Worker {self.rank}: Error during serialization: {str(e)}")
			# Re-raise the exception after logging
			raise
		finally:
			# Always attempt to clean up temporary files
			try:
				self.serializer.cleanup()
				logger.debug(f"Worker {self.rank}: Cleanup complete")
			except Exception as e:
				logger.error(f"Worker {self.rank}: Error during cleanup: {str(e)}")
				# Don't re-raise cleanup errors
				
		# Final barrier to ensure all processes are done before proceeding
		self.comm.Barrier()
		
	def produce(self) -> Optional[Batch]:
		'''
		Once the results have been serialized, this stage is used as the input stream.
		'''
		# Safely open the file with retries to handle potential file locking issues
		max_retries = 3
		retry_delay = 0.2
		
		for attempt in range(max_retries):
			try:
				with h5py.File(self.cfg['file'], 'r') as savefile:
					# Check file path for validation tracking
					file_path = os.path.abspath(self.cfg['file'])
					
					# Only validate once per file
					if self.checked_data_file != file_path:
						self.checked_data_file = file_path
						
						# Let the loader's validation handle the check
						# This centralizes the validation logic in the BatchLoader class
						return self.loader.load(savefile)
					else:
						# Skip validation on subsequent loads of the same file
						return self.loader.load(savefile)
						
			except BlockingIOError as e:
				if attempt < max_retries - 1:
					logger.debug(f"Worker {self.rank}: File access retry {attempt+1}/{max_retries} after {retry_delay}s delay")
					time.sleep(retry_delay)
					retry_delay *= 2  # Exponential backoff
				else:
					logger.error(f"Worker {self.rank}: Failed to open file after {max_retries} attempts")
					raise


