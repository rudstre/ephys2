'''
Base append-only storage mechanism for datasets in HDF5.
See types.py for the type definitions.

TODO: move away from POSIX-specific filepaths.
TODO: exception safety

See H5Serializer's Public API for the intended workflow (below).
'''

from typing import Union, Optional, Tuple, Any, List, Generator
from collections.abc import Iterable
import h5py
import numpy as np
import numpy.typing as npt
from abc import ABC, abstractmethod
import os
import shutil
import itertools
import shortuuid

from ephys2.lib.types import *
from ephys2.lib.mpi import MPI
from ephys2.lib.singletons import logger, global_metadata, global_state
from ephys2.lib.utils import is_file_writeable
from .utils import *
from .tags import *

MultiIndex = Tuple[Union[ID_DTYPE, 'MultiIndex'], ...]
MultiData = Tuple[Union[Batch, npt.NDArray], ...]

class H5Serializer(ABC):
	'''
	Base class for serializing sequential batches of data with offset-tracking mechanisms within an HDF5 file.
	The inheritance hierarchy implicitly enables partial writes.
	'''
	def __init__(self, full_check=False, rank=None, n_workers=None):

		# MPI
		self.comm = MPI.COMM_WORLD
		self.rank = self.comm.Get_rank() if rank is None else rank
		self.n_workers = self.comm.Get_size() if n_workers is None else n_workers
		assert 0 <= self.rank < self.n_workers, 'Inconsistent rank and n_workers'

		# Parameters
		self.full_check = full_check # Whether to conduct full checks of the data

		# State
		self.is_chunks_initialized = False # Whether the serializer is ready to write chunks
		self.is_initialized = False # Whether initialize() has been called

	''' 
	Public API 

	Workflow:
		1. call initialize() 
		2. Call write() any number of times from parallel workers
		3. Call serialize() once after all workers have completed writing chunks
		4. Call cleanup() to delete temporary files
	'''

	def initialize(self, out_path: RWFilePath):
		'''
		Initialize the filesystem structure 
		'''
		# Create filesystem layout
		self.out_path = out_path
		outer_wd = os.path.dirname(out_path)
		tmp_name = f'tmp_ephys2_NODELETE_{shortuuid.uuid()}_{os.path.basename(out_path)}'
		tmp_path = f'{outer_wd}/{tmp_name}' # Working directory for temporary worker files

		if self.rank == 0:
			# Check that we have write access to output file
			if not is_file_writeable(self.out_path):
				raise ValueError(f'Path {self.out_path} is not writeable by this user. Obtain the permissions, change user, or change the save path.')

			# Warn if the output file already exists
			if os.path.exists(self.out_path):
				if global_state.last_h5 == self.out_path:
					logger.warn(f'Output file {self.out_path} already exists, it will be modified.')
				else:
					logger.warn(f'Output file {self.out_path} already exists, deleting.')
					os.remove(self.out_path)
			else:
				logger.print(f'Output file {self.out_path} does not exist, creating.')

			# Check that we have write access to the temporary directory
			try:
				open(tmp_path, 'w')
			except PermissionError:
				raise ValueError(f'Directory {outer_wd} is not writeable by this user. Obtain the permissions, change user, or change the directory.')
			except IsADirectoryError:
				logger.warn(f'Found existing temporary working directory {tmp_path}, deleting.')
				shutil.rmtree(tmp_path)
			else:
				os.remove(tmp_path)
			os.mkdir(tmp_path)

		# Wait for filesystem layout to be initialized
		self.comm.Barrier()

		# Broadcast working directory to all workers
		self.tmp_path = self.comm.bcast(tmp_path, root=0)
		self.filepath = self.get_worker_path(self.rank)

		# Do all work in temporary file-per-process
		if os.path.exists(self.filepath):
			logger.warn(f'{self.filepath} exists, removing.')
			os.remove(self.filepath)

		self.is_initialized = True

	def write(self, data: Any):
		'''
		Write chunks to file-per-process
		'''
		assert self.is_initialized, 'Tried to write chunks without initialization'
		with h5py.File(self.filepath, 'a') as h5dir:
			if not self.is_chunks_initialized:
				# Obtain existing file, if it exists, to determine who in the lineage must write
				if os.path.exists(self.out_path):
					with h5py.File(self.out_path, 'r') as out_file:
						self.init_chunks_passthrough(h5dir, out_file, data)
				else:
					self.init_chunks_passthrough(h5dir, None, data)
				self.is_chunks_initialized = True
			self.write_chunk_passthrough(h5dir, data)

	def serialize(self):
		'''
		Serialize the chunks into the final output, using MPI I/O
		'''
		self.comm.Barrier() # Wait for workers to complete

		with open_h5s(self.get_chunk_paths(), 'r') as in_dirs: # These files are opened in read-mode, they should always close successfully.

			# Read size info from worker files
			if self.is_chunks_initialized:
				self.read_chunks_info_passthrough(in_dirs)

			# Initialize output file (this creates structure & sets any metadata - from single writer process)
			if self.rank == 0:
				assert self.is_chunks_initialized, 'Impossible: cannot run a serialization with no data at all'
				with h5py.File(self.out_path, 'a') as out_dir:
					self.init_serialize_passthrough(out_dir)

			# Wait for serialize initialization
			self.comm.Barrier()

			# If more than 1 worker, open in MPI write mode.
			# Opening this file from all processes is necessary, regardless of available work.
			# We don't use the with() contextmanager here since the parallel file close can block if an exception is thrown during serialization.
			out_dir = h5py.File(self.out_path, 'a', driver='mpio', comm=self.comm) 
			if self.is_chunks_initialized:
				self.run_serialize_passthrough(in_dirs[self.rank], out_dir)
			else:
				# We abuse the check() method to make Parallel HDF5 think the idle workers are also 
				# participating in the writes. This causes writes from all workers to flush properly.
				# Without this, the writes from the other conditional branch ^ will hang.
				# See https://github.com/h5py/h5py/issues/965 for a possibly related issue.
				self.check(out_dir)
			out_dir.close()

			# Wait to finish serializing
			self.comm.Barrier()

			# Run the post-serialization
			if self.rank == 0:
				with h5py.File(self.out_path, 'a') as out_dir:
					# Write currently available global metadata to the file
					out_dir.attrs['metadata'] = global_metadata.to_string()
					if self.full_check:
						self.check(out_dir, full=True)
						logger.print(f'Check passed: {self.out_path}')
				logger.print(f'Finished writing: {self.out_path}')

		# Wait for the post-serialization
		self.comm.Barrier()

		# Update last path
		global_state.last_h5 = self.out_path

	def cleanup(self):
		'''
		Delete temporary files
		'''
		if self.rank == 0:
			shutil.rmtree(self.tmp_path)

	'''
	Data type information
	'''

	@classmethod
	@abstractmethod
	def data_type(cls) -> type:
		'''
		Return the data type of the data to be serialized
		'''
		pass

	@classmethod
	def load_type(cls) -> type:
		'''
		For serializers whose inputs and outputs are of different types, a separate load_type which is normally the same as data_type.
		'''
		return cls.data_type()

	@classmethod
	def tag(cls: type) -> str:
		'''
		Return the tag for this data type
		'''
		return cls.data_type().__name__

	@classmethod
	@abstractmethod
	def version(cls:  type) -> int:
		'''
		Return the version for this data type
		'''
		pass

	@classmethod
	def fields(cls: type) -> List[str]:
		'''
		Return the HDF5 datasets/groups written for this data type 
		(only additional fields beyond the parent class)
		'''
		return []

	@classmethod
	def attrs(cls: type) -> List[str]:
		'''
		Return the HDF5 attributes for this data type
		(only additional attributes beyond the parent class)
		'''
		return []

	@classmethod
	def parent(cls: type) -> type:
		'''
		Return the parent serializer for this serializer
		'''
		return H5Serializer

	@property
	def chunksize(self) -> int:
		'''
		Chunk size for both worker and final output files
		'''
		return 512

	''' 
	Serialization procedure overrides (type-specific); only write the additional 
	data pertinent to the type's lineage. (E.g. LVBatch writes only labels, not VBatch's time and data fields.)
	''' 

	def init_chunks(self, h5dir: H5Dir, data: Any):
		'''
		Initialize the HDF5 file structure.
		h5dir should be passed in a writeable mode.
		'''
		pass

	def write_chunk(self, h5dir: H5Dir, data: Any):
		'''
		Write a single batch of data.
		h5dir should be passed in a writeable mode.
		'''
		pass

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		'''
		Iterate over written chunks.
		h5dir should be passed in a readable mode.
		'''
		return itertools.repeat(None)

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		'''
		Initialize state from shards.
		in_dirs: readable source directories for all instances of H5Serializer
		'''
		pass

	def init_serialize(self, out_dir: H5Dir):
		'''
		Create HDF5 structure of output file.
		out_dir: writeable destination directory (should not be opened in MPI mode, this changes the file structure)
		'''
		pass

	def start_serialize(self) -> MultiIndex:
		'''
		Get the starting position for writes.
		'''
		return None

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		'''
		Write a batch of data to the trailing edge; should only be called in batch order.
		Returns the next (canonical; may be modified) MultiIndex to be written at. 
		out_dir should be passed in a writeable mode.
		'''
		return iat

	@classmethod
	@abstractmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		'''
		Check the format of the stored data.
		full=True should only be used in test cases, since may load all data into memory.

		We also (ab)use this method to ensure MPI writes are flushed properly; without 
		performing certain specific reads on the written data, the process hangs on close.
		Appears to be an issue with h5py.
		See serialize.py for the exact use cases.
		May be related to this issue: https://github.com/h5py/h5py/issues/965
		'''
		pass

	'''
	Recursive private methods calling overrides
	'''

	@classmethod
	def should_write(cls: type, out_dir: H5Dir) -> bool:
		'''
		Return whether this type should write to the given directory.
		(Returns yes if any of the fields are missing)
		'''
		fields = set(out_dir.keys())
		attrs = set(out_dir.attrs.keys())
		return not (
			all(f in fields for f in cls.fields()) and
			all(a in attrs for a in cls.attrs())
		)

	def init_lineage(self, out_dir: Optional[H5Dir]):
		'''
		Initialize the lineage, along with who in the lineage will write.
		'''
		# Lineage (used for partial serialization)
		self.lineage = []
		current_node = self.__class__
		while not (current_node is H5Serializer):
			self.lineage.append(current_node)
			current_node = current_node.parent()
		self.lineage.reverse()
		assert len(self.lineage) > 0
		logger.debug('Lineage:', [c.__name__ for c in self.lineage])
		
		# Members of lineage who should write
		self.lineage_writers = [
			(
				out_dir is None or 
				cls.should_write(out_dir) or
				i == len(self.lineage) - 1
			)
			for i, cls in enumerate(self.lineage)
		]
		logger.debug('Lineage writers:', self.lineage_writers)

	def init_chunks_passthrough(self, h5dir: H5Dir, out_dir: Optional[H5Dir], data: Any):
		self.init_lineage(out_dir)
		for cls, writer in zip(self.lineage, self.lineage_writers):
			if writer:
				cls.init_chunks(self, h5dir, data)

	def write_chunk_passthrough(self, h5dir: H5Dir, data: Any):
		for cls, writer in zip(self.lineage, self.lineage_writers):
			if writer:
				cls.write_chunk(self, h5dir, data)

	def iter_chunks_passthrough(self, h5dir: H5Dir) -> Gen[MultiData]:
		return zip(
			*(
				cls.iter_chunks(self, h5dir) if writer else itertools.repeat(None)
				for cls, writer in zip(self.lineage, self.lineage_writers)
			)
		)

	def read_chunks_info_passthrough(self, in_dirs: List[H5Dir]):
		for cls, writer in zip(self.lineage, self.lineage_writers):
			if writer:
				cls.read_chunks_info(self, in_dirs)

	def init_serialize_passthrough(self, out_dir: H5Dir):
		for cls, writer in zip(self.lineage, self.lineage_writers):
			if writer:
				cls.init_serialize(self, out_dir)
				
		# Write type & version information
		out_dir.attrs['tag'] = type(self).tag()
		out_dir.attrs['version'] = type(self).version()

	def start_serialize_passthrough(self) -> MultiIndex:
		return tuple(
			cls.start_serialize(self) if writer else None
			for cls, writer in zip(self.lineage, self.lineage_writers)
		)

	def advance_serialize_passthrough(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		return tuple(
			cls.advance_serialize(self, out_dir, idx, datum) if not (idx is None) else None
			for cls, idx, datum in zip(self.lineage, iat, data)
		)

	'''
	Main serialization loop
	'''

	def run_serialize_passthrough(self, in_dir: H5Dir, out_dir: H5Dir):
		'''
		Run the serialization procedure transferring chunks from the worker file to the final output file.
		'''
		iat = self.start_serialize_passthrough()
		for data in self.iter_chunks_passthrough(in_dir):
			iat = self.advance_serialize_passthrough(out_dir, iat, data)

	''' 
	Private API 
	''' 

	def get_worker_path(self, rank) -> RWFilePath:
		''' Get the working directory of a worker '''
		return f'{self.tmp_path}/rank_{rank}.h5'

	def get_chunk_paths(self) -> List[ROFilePath]:
		paths = [self.get_worker_path(i) for i in range(self.n_workers)]
		# Worker i may not have done any work if i > self.rank
		return [p for p in paths if os.path.exists(p)]

	'''
	Loader methods
	'''

	@classmethod
	def check_tag_version(cls: type, h5dir: H5Dir):
		'''
		Check that the tag and version match the expected values.
		'''
		assert 'tag' in h5dir.attrs, 'Datatype tag missing'
		assert 'version' in h5dir.attrs, 'Datatype version missing'
		tag = h5dir.attrs['tag']
		version = h5dir.attrs['version']
		data_class = class_tag_map[tag]
		loader_class = class_tag_map[cls.tag()]
		if not (issubclass(data_class, loader_class) or (data_class is SLLVBatch and loader_class is SLVBatch)): 
			raise ValueError(f'Tag mismatch: {cls.tag()} cannot be read from data type {tag}')
		if version != cls.version():
			raise ValueError(f'Version mismatch: {version} != {cls.version()}')

	@classmethod
	@abstractmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		pass

	@classmethod
	@abstractmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> Any:
		pass

	@classmethod
	@abstractmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> Any:
		pass

	@classmethod
	@abstractmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> Any:
		pass

	'''
	Serializer for MultiBatch data.
	'''

class H5MultiSerializer(H5Serializer):

	@classmethod
	@abstractmethod
	def item_serializer(cls: type) -> type:
		'''
		The serializer for each item in the dictionary.
		'''
		pass

	'''
	Private recursive method overrides
	'''

	def init_chunks_passthrough(self, h5dir: H5Dir, out_dir: Optional[H5Dir], data: MultiBatch):
		self.serializers = dict()
		self.item_ids = list(data.items.keys())
		for item_id in self.item_ids:
			item_dir = h5dir.create_group(item_id)
			out_item_dir = None if (out_dir is None or not(item_id in out_dir.keys())) else out_dir[item_id]
			self.serializers[item_id] = self.item_serializer()(self.full_check, self.rank, self.n_workers)
			self.serializers[item_id].init_chunks_passthrough(item_dir, out_item_dir, data.items[item_id])

	def write_chunk_passthrough(self, h5dir: H5Dir, data: MultiBatch):
		for item_id, item in data.items.items():
			self.serializers[item_id].write_chunk_passthrough(h5dir[item_id], item)

	def iter_chunks_passthrough(self, h5dir: H5Dir) -> Gen[MultiData]:
		return zip(
			*(self.serializers[item_id].iter_chunks_passthrough(h5dir[item_id]) for item_id in self.item_ids)
		)

	def read_chunks_info_passthrough(self, in_dirs: List[H5Dir]):
		assert len(in_dirs) > 0
		for item_id, serializer in self.serializers.items():
			serializer.read_chunks_info_passthrough([in_dir[item_id] for in_dir in in_dirs])

	def init_serialize_passthrough(self, out_dir: H5Dir):
		for item_id, serializer in self.serializers.items():
			out_item_dir = out_dir[item_id] if item_id in out_dir else out_dir.create_group(item_id)
			serializer.init_serialize_passthrough(out_item_dir)
				
		# Write type & version information
		out_dir.attrs['tag'] = type(self).tag()
		out_dir.attrs['version'] = type(self).version()
		logger.debug(f'Wrote tag {out_dir.attrs["tag"]} version {out_dir.attrs["version"]}')

	def start_serialize_passthrough(self) -> MultiIndex:
		return tuple(
			serializer.start_serialize_passthrough() for serializer in self.serializers.values()
		)
	
	def advance_serialize_passthrough(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		return tuple(
			self.serializers[item_id].advance_serialize_passthrough(
				out_dir[item_id], idx, datum
			) for item_id, idx, datum in zip(self.item_ids, iat, data)
		)

	'''
	Public API overrides
	'''

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		for item_id in h5dir.keys():
			cls.item_serializer().check(h5dir[item_id], full)

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> Dict[str, int]:
		return {
			item_id: cls.item_serializer().get_size(h5dir[item_id]) 
			for item_id in h5dir.keys()
		}

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> MultiBatch:
		return cls.load_type()(
			items = {
				item_id: cls.item_serializer().load(h5dir[item_id], start, stop, overlap)
				for item_id in h5dir.keys()
			}
		)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> MultiBatch:
		'''
		Note: the indices will be used uniformly across all streams.
		'''
		return cls.load_type()(
			items = {
				item_id: cls.item_serializer().load_sparse(h5dir[item_id], indices)
				for item_id in h5dir.keys()
			}
		)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> MultiBatch:
		return cls.load_type()(
			items = {
				item_id: cls.item_serializer().load_multi([h5dir[item_id] for h5dir in h5dirs], start, stop, overlap, time_offsets)
				for item_id in h5dirs[0].keys()
			}
		)