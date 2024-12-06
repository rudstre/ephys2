'''
HDF5 Stream serializer for array types.
'''
from typing import Optional
import numpy as np
import numpy.typing as npt
import pdb

from .base import *
from ephys2.lib.array import mkshape

class H5ArraySerializer(H5Serializer):

	def __init__(self, name: str, full_check=False, rank=None, n_workers=None):
		self.name = name # Array serializer requires a name
		self.chunk_ctr = 0 # Chunk write counter
		super().__init__(full_check=full_check, rank=rank, n_workers=n_workers)

	@classmethod
	def data_type(cls: type) -> type:
		return np.ndarray

	@classmethod
	def version(cls: type) -> int:
		return 0

	def init_chunks(self, h5dir: H5Dir, data: npt.NDArray):
		ndim = data.shape[1] if len(data.shape) == 2 else 1
		dtype = data.dtype
		h5dir.create_dataset('data', shape=mkshape(0, ndim), maxshape=mkshape(None, ndim), chunks=mkshape(self.chunksize, ndim), dtype=dtype)
		# Endstops are stored with a leading 0
		h5dir.create_dataset('endstops', shape=(1,), maxshape=(None,), data=np.array([0], dtype=ID_DTYPE), chunks=(self.chunksize,), dtype=ID_DTYPE)

	def write_chunk(self, h5dir: H5Dir, data: npt.NDArray):
		old_size = h5dir['data'].shape[0]
		new_size = old_size + data.shape[0]
		h5dir['data'].resize(new_size, axis=0)
		h5dir['endstops'].resize(self.chunk_ctr + 2, axis=0)
		h5dir['data'][old_size:] = data
		h5dir['endstops'][self.chunk_ctr + 1] = new_size 
		self.chunk_ctr += 1

	def iter_chunks(self, h5dir: H5Dir) -> Gen[npt.NDArray]:
		N = h5dir['endstops'].shape[0] - 1
		for n in range(N):
			start, stop = h5dir['endstops'][n], h5dir['endstops'][n+1]
			yield h5dir['data'][start:stop]

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		assert len(in_dirs) > 0
		my_dir = in_dirs[self.rank]
		self.M = 0 if len(my_dir['data'].shape) == 1 else my_dir['data'].shape[1]
		self.N = 0
		self.P = len(in_dirs) # Number of partitions
		self.all_endstops = []
		for in_dir in in_dirs:
			self.N += in_dir['data'].shape[0]
			self.all_endstops.append(in_dir['endstops'][:])
		self.dtype = my_dir['data'].dtype

	def init_serialize(self, out_dir: H5Dir):
		shape = (self.N,) if self.M == 0 else (self.N, self.M)
		if self.N > self.chunksize:
			assert self.chunksize > 0
			chunks = (self.chunksize,) if self.M == 0 else (self.chunksize, self.M)
		else:
			chunks = None
		dataset = create_overwrite_dataset(out_dir, self.name, shape, dtype=self.dtype, chunks=chunks)
		super().init_serialize(dataset)

	def start_serialize(self) -> MultiIndex:
		self.serialize_ctr = 0
		self.serialize_ctr_max = self.all_endstops[self.rank].shape[0] - 2 # Endstops has leading 0
		iat = 0 # Offset in output dataset
		for i in range(self.rank):
			j = 1 if (self.all_endstops[i].size > 1) else 0 # Skip leading 0, unless previous partitions had no data.
			iat += self.all_endstops[i][j]
		return iat

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, data: npt.NDArray):
		if type(out_dir) != h5py.Dataset:
			out_dir = out_dir[self.name] # Allow top-level serialization
		out_dir[iat:iat + data.shape[0]] = data
		if self.serialize_ctr < self.serialize_ctr_max: # Any more data from this partition to be written
			for i in range(self.rank, self.P):
				iat += self.all_endstops[i][self.serialize_ctr + 1] - self.all_endstops[i][self.serialize_ctr] # Count offsets after me
			for i in range(self.rank):
				iat += self.all_endstops[i][self.serialize_ctr + 2] - self.all_endstops[i][self.serialize_ctr + 1] # Count offets before me
		self.serialize_ctr += 1
		return iat

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		return

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir.shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> npt.NDArray:
		overlap = 0 if (start is None or start == 0) else overlap
		data = h5dir[start:stop]
		if overlap >= data.shape[0]: # We have seen this data before.
			shape = list(data.shape)
			shape[0] = 0
			return np.empty(tuple(shape), dtype=data.dtype)
		return data

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, offsets: Optional[List[int]]=None) -> npt.NDArray:
		N_dirs = len(h5dirs)
		assert N_dirs > 0, 'Pass at least one data directory to load_multi'
		dir_sizes = [h5dir.shape[0] for h5dir in h5dirs]
		size = sum(dir_sizes)
		start = 0 if start is None else start
		stop = size if stop is None else stop
		overlap = 0 if start == 0 else overlap
		if start >= size or overlap >= size or stop <= start:
			shape = list(h5dirs[0].shape)
			shape[0] = 0
			return np.empty(tuple(shape), dtype=h5dirs[0].dtype)
		else:
			data = []
			for i in range(N_dirs):
				if start < dir_sizes[i] and stop > 0:
					act_start = max(0, start)
					act_stop = min(stop, dir_sizes[i])
					query = h5dirs[i][act_start:act_stop]
					if not (offsets is None):
						query += offsets[i] # Query data with possible offset
					data.append(query)
				start -= dir_sizes[i]
				stop -= dir_sizes[i]
			data = np.concatenate(data, axis=0)
			if overlap >= data.shape[0]: # We have seen this data before.
				shape = list(data.shape)
				shape[0] = 0
				return np.empty(tuple(shape), dtype=data.dtype)
			return data

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> npt.NDArray:
		return h5dir[indices]

