'''
Storing scipy sparse matrices as HDF5 groups
'''

from typing import Optional, Tuple
import h5py
import numpy as np
import numpy.typing as npt
import scipy.sparse as sp
import pdb

from .base import *
from .array import *
from ephys2.lib.sparse import *
from ephys2.lib.array import *

class H5CSRSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return CSRMatrix

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['data', 'indices', 'indptr']

	@classmethod
	def attrs(cls: type) -> List[str]:
		return ['shape']

	def init_chunks(self, h5dir: H5Dir, data: CSRMatrix):
		self.shapes_serializer = H5ArraySerializer('shapes', self.full_check, self.rank, self.n_workers)
		self.data_serializer = H5ArraySerializer('data', self.full_check, self.rank, self.n_workers)
		self.indices_serializer = H5ArraySerializer('indices', self.full_check, self.rank, self.n_workers)
		self.indptr_serializer = H5ArraySerializer('indptr', self.full_check, self.rank, self.n_workers)

		self.shapes_serializer.init_chunks(h5dir.create_group('shapes'), np.array([data.shape]))
		self.data_serializer.init_chunks(h5dir.create_group('data'), data.data)
		self.indices_serializer.init_chunks(h5dir.create_group('indices'), data.indices)
		self.indptr_serializer.init_chunks(h5dir.create_group('indptr'), data.indptr)

	def write_chunk(self, h5dir: H5Dir, data: CSRMatrix):
		self.shapes_serializer.write_chunk(h5dir['shapes'], np.array([data.shape]))
		self.data_serializer.write_chunk(h5dir['data'], data.data)
		self.indices_serializer.write_chunk(h5dir['indices'], data.indices)
		self.indptr_serializer.write_chunk(h5dir['indptr'], data.indptr) 

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return zip(
			self.data_serializer.iter_chunks(h5dir['data']),
			self.indices_serializer.iter_chunks(h5dir['indices']),
			self.indptr_serializer.iter_chunks(h5dir['indptr']),
		)

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.data_serializer.read_chunks_info([in_dir['data'] for in_dir in in_dirs])
		self.indices_serializer.read_chunks_info([in_dir['indices'] for in_dir in in_dirs])
		self.indptr_serializer.read_chunks_info([in_dir['indptr'] for in_dir in in_dirs])
		Nshards = len(self.indptr_serializer.all_endstops)
		# Count the extraneous leading zeros; we do so by counting the number of batches
		# (endstops itself has a leading zero), and subtracting one for the actual leading 0 to be written.
		Nzeros = np.concatenate(self.indptr_serializer.all_endstops).size - Nshards - 1 
		self.indptr_serializer.N -= Nzeros # Remove leading zeros from indptr batches
		self.N, self.M = 0, 0
		for in_dir in in_dirs:
			shapes = in_dir['shapes']['data'][:]
			self.N += shapes.sum(axis=0)[0]
			M_ = 0 if shapes.shape[0] == 0 else shapes.max(axis=0)[1]
			self.M = max(self.M, M_) # Appending matrices results in expansion of the 2nd dimension
		self.P = len(in_dirs)

	def init_serialize(self, out_dir: H5Dir):
		self.data_serializer.init_serialize(out_dir)
		self.indices_serializer.init_serialize(out_dir)
		self.indptr_serializer.init_serialize(out_dir)
		out_dir.attrs['shape'] = (self.N, self.M)

	def start_serialize(self) -> MultiIndex:
		self.serialize_ctr = 0
		i1 = self.data_serializer.start_serialize()
		i2 = self.indices_serializer.start_serialize()
		i3 = self.indptr_serializer.start_serialize() 
		i3 -= max(0, self.rank - 1) # Remove intermediate leading zeros
		return (i1, i2, i3)

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, matrix: MultiData) -> MultiIndex:
		(i1, i2, i3) = iat
		(data, indices, indptr) = matrix
		# Append mode: offset indptr by existing data
		if self.serialize_ctr == 0 and self.rank == 0:
			# First batch, first worker: keep leading 0
			assert i1 == i2 == i3 == 0
			i3 = self.indptr_serializer.advance_serialize(out_dir['indptr'], i3, indptr)
			i3 -= (self.P - 1) # Remove intermediate leading zeros, accounting for the fact that I just wrote one
		else:
			# Otherwise, suppress leading conventional 0 of indptr
			i3 = self.indptr_serializer.advance_serialize(out_dir['indptr'], i3, indptr[1:] + i1) 
			i3 -= self.P # Remove intermediate leading zeros
		i2 = self.indices_serializer.advance_serialize(out_dir['indices'], i2, indices)
		i1 = self.data_serializer.advance_serialize(out_dir['data'], i1, data)
		self.serialize_ctr += 1
		return (i1, i2, i3)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		'''
		Check the consistency of stored data.
		Replicates https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.check_format.html
		'''
		assert h5dir.attrs['shape'][0] == h5dir['indptr'].shape[0] - 1
		assert h5dir['indices'].shape == h5dir['data'].shape
		H5ArraySerializer.check(h5dir['data'], full)
		H5ArraySerializer.check(h5dir['indices'], full)
		H5ArraySerializer.check(h5dir['indptr'], full)
		if full:
			assert h5dir['indptr'][-1] == h5dir['indices'].shape[0]
			indptr = h5dir['indptr'][:]
			indices = h5dir['indices'][:]
			# Check the consistency of indices and indptr
			# Check that indptr is nondecreasing
			assert (np.diff(indptr) >= 0).all()
			# Check dimensions of indices
			if indices.size > 0:
				assert indices.min() >= 0
				assert indices.max() < h5dir.attrs['shape'][1]
			data = H5CSRSerializer.load(h5dir)
			# Do the check once more, once the data is actually loaded. (The two are not equivalent due to silent re-sizing by scipy.)
			data.check_format()

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir.attrs['shape'][0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> CSRMatrix:
		'''
		Note: if loading partially, the indptr will be automatically re-started at 0.
		'''
		if start == stop == None:
			return CSRMatrix(h5dir['data'][:], h5dir['indices'][:], h5dir['indptr'][:], h5dir.attrs['shape'])
		stop = h5dir.attrs['shape'][0] if stop is None else stop
		overlap = 0 if (start is None or start == 0) else overlap
		# Indptr is stored with conventional leading zero
		indptr = h5dir['indptr'][start:stop + 1] 
		if indptr.size == 0:
			return empty_csr(h5dir.attrs['shape'][1], dtype=h5dir['data'].dtype)
		elif overlap > 0 and indptr.size <= overlap + 1: # We have seen this data before.
			return empty_csr(h5dir.attrs['shape'][1], dtype=h5dir['data'].dtype)
		else:
			# Read rows from indptr
			indices = h5dir['indices'][indptr[0]:indptr[-1]]
			data = h5dir['data'][indptr[0]:indptr[-1]]
			indptr -= indptr[0] # Apply row offset
			# Get shape
			N, M = indptr.size - 1, h5dir.attrs['shape'][1]
			return CSRMatrix(data, indices, indptr, (N, M))

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> CSRMatrix:
		'''
		The CSR sparse loader will select rows of the matrix individually.
		'''
		if indices.size > 0:
			starts = h5dir['indptr'][indices]
			stops = h5dir['indptr'][indices + 1]
			inbetween = arange2d(starts, stops)
			data = h5dir['data'][inbetween]
			indices = h5dir['indices'][inbetween]
			delta = stops - starts
			indptr = np.insert(np.cumsum(delta), 0, 0)
			N, M = indptr.size - 1, h5dir.attrs['shape'][1]
			return CSRMatrix(data, indices, indptr, (N, M))
		else:
			return empty_csr(h5dir.attrs['shape'][1], dtype=h5dir['data'].dtype)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> CSRMatrix:
		N_dirs = len(h5dirs)
		assert N_dirs > 0, 'Pass at least one data directory to load_multi'
		dir_sizes = [h5dir.attrs['shape'][0] for h5dir in h5dirs]
		size = sum(dir_sizes)
		start = 0 if start is None else start
		stop = size if stop is None else stop
		overlap = 0 if start == 0 else overlap
		if start >= size or overlap >= size or stop <= start:
			return empty_csr(h5dirs[0].attrs['shape'][1], dtype=h5dirs[0]['data'].dtype)
		else:
			data = []
			for i in range(N_dirs):
				if start < dir_sizes[i] and stop > 0:
					act_start = max(0, start)
					act_stop = min(stop, dir_sizes[i])
					data.append(H5CSRSerializer.load(h5dirs[i], start=act_start, stop=act_stop, overlap=0))
				start -= dir_sizes[i]
				stop -= dir_sizes[i]
			data = csr_concat(data)
			return data

	@classmethod
	def replace(cls: type, h5dir: H5Dir, mat: CSRMatrix):
		del h5dir['data']
		del h5dir['indices']
		del h5dir['indptr']
		h5dir.attrs['shape'] = mat.shape
		h5dir.create_dataset('data', data=mat.data)
		h5dir.create_dataset('indices', data=mat.indices)
		h5dir.create_dataset('indptr', data=mat.indptr)
