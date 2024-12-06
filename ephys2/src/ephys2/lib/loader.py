'''
Parallel loading of Batch data in chunks.
See ./types.py for the type definitions.
'''
import h5py
import time
import warnings
import pdb
from abc import ABC, abstractmethod
from typing import Optional

from ephys2.lib.utils import ext_mul
from ephys2.lib.h5 import *
from ephys2.lib.types import *
from ephys2.lib.singletons import global_state

class BatchLoader(ABC):
	'''
	Base class for loading in ordered chunks.
	'''
	def __init__(self, rank: int, n_workers: int, start: int, stop: int, batch_size: int, batch_overlap: int):
		'''
		rank: id of the reader
		n_workers: total number of parallel reader
		start: start index
		stop: stop index (can be infinite to load all the data)
		batch_size: size of each chunk to read (can be infinite to load all data at once)
		batch_overlap: amount of trailing-edge overlap between loaded batches (total data size will still be batch_size)

		This method should not be overridden.
		'''
		assert 0 <= rank < n_workers, 'Inconsistent rank and n_workers'
		assert 0 <= start <= stop, 'Start and stop inconsistent'
		assert batch_overlap < np.inf, 'Batch overlap cannot be infinite'
		assert batch_overlap < batch_size, 'Batch overlap must be at least one less than batch size in order to make progress'
		self.rank = rank
		self.n_workers = n_workers
		self.start = start
		self.stop = stop
		self.batch_size = batch_size
		self.batch_overlap = batch_overlap
		self.load_index = self.start + ext_mul(self.rank, self.batch_size - self.batch_overlap)
		self.load_params_set = False

	@property
	@abstractmethod
	def loader(self) -> H5Serializer:
		'''
		Return the correct loader
		'''
		pass

	@abstractmethod
	def is_empty(self, data: Batch) -> bool:
		'''
		Used to determine when to terminate
		'''
		pass

	def load(self, files: Union[h5py.File, List[h5py.File]], time_offsets: Optional[List[int]]=None) -> Optional[Batch]:
		'''
		Load a chunk of data from the serialized file.
		Should be called after serialize().
		'''
		# Set global loading state
		if not self.load_params_set:
			global_state.load_start = self.start
			global_state.load_size = self.compute_load_size(files)
			global_state.load_overlap = self.batch_overlap
			global_state.load_batch_size = self.batch_size
			self.load_params_set = True
		global_state.load_index = self.load_index # Update the load index
		
		# Load data 
		if self.load_index + self.batch_overlap < self.stop: # Load data if we haven't seen it before
			next_stop = min(self.load_index + self.batch_size, self.stop)
			data = None
			if self.load_index < np.inf and self.load_index < next_stop:
				next_stop = None if next_stop == np.inf else next_stop
				if type(files) is list:
					if len(files) == 1: # Avoid unnecessary concatenation
						data = self.loader.load(files[0], start=self.load_index, stop=next_stop, overlap=self.batch_overlap)
					else:
						data = self.loader.load_multi(files, start=self.load_index, stop=next_stop, overlap=self.batch_overlap, time_offsets=time_offsets)
				else:
					data = self.loader.load(files, start=self.load_index, stop=next_stop, overlap=self.batch_overlap)
				data = None if self.is_empty(data) else data
			self.load_index += self.n_workers * (self.batch_size - self.batch_overlap) # Advance to next block for this worker 
			return data

	def compute_load_size(self, files: Union[h5py.File, List[h5py.File]]) -> Union[int, Dict[str, int]]:
		if not (type(files) is list):
			files = [files]
		size = 0
		for f in files:
			f_size = self.loader.get_size(f)
			if type(f_size) is int:
				size += f_size
			elif type(f_size) is dict:
				if size == 0:
					size = f_size
				else:
					for k in f_size:
						size[k] += f_size[k]
			else:
				raise TypeError('Unsupported file size type: {}'.format(type(f_size)))
		if type(size) is int:
			return min(self.stop, size) - self.start
		else:
			return {
				k: min(self.stop, size[k]) - self.start
				for k in size
			}

'''
Type-dependent loaders
'''

class SBatchLoader(BatchLoader):

	@property
	def loader(self) -> H5Serializer:
		return H5SBatchSerializer

	def is_empty(self, data: SBatch) -> bool:
		return data.size == 0


class VMultiBatchLoader(BatchLoader):

	@property
	def loader(self) -> H5Serializer:
		return H5VMultiBatchSerializer

	def is_empty(self, data: VMultiBatch) -> bool:
		return all(item.size == 0 for item in data.items.values())


class LVMultiBatchLoader(BatchLoader):

	@property
	def loader(self) -> H5Serializer:
		return H5LVMultiBatchSerializer

	def is_empty(self, data: LVMultiBatch) -> bool:
		return all(item.size == 0 for item in data.items.values())


class LLVMultiBatchLoader(BatchLoader):

	@property
	def loader(self) -> H5Serializer:
		return H5LLVMultiBatchSerializer

	def is_empty(self, data: LLVMultiBatch) -> bool:
		return all(item.size == 0 for item in data.items.values())


class SLLVMultiBatchLoader(BatchLoader):

	@property
	def loader(self) -> H5Serializer:
		return H5SLLVMultiBatchSerializer

	def is_empty(self, data: SLLVMultiBatch) -> bool:
		return all(item.size == 0 for item in data.items.values())


class LTMultiBatchLoader(BatchLoader):

	@property
	def loader(self) -> H5Serializer:
		return H5LTMultiBatchSerializer

	def is_empty(self, data: LTMultiBatch) -> bool:
		return all(item.size == 0 for item in data.items.values())

