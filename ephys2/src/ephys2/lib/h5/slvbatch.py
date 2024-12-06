'''
HDF5 serializer for summarized labeled vector batch.
'''

from .array import *
from .lvbatch import *

from ephys2.lib.types.sllvbatch import *

class H5SLVBatchSerializer(H5LVBatchSerializer):

	@classmethod
	def data_type(cls: type) -> type:
		return SLVBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['variance', 'difftime', 'indices']

	@classmethod
	def parent(cls: type) -> type:
		return H5LVBatchSerializer

	def init_chunks(self, h5dir: H5Dir, data: SLVBatch):
		self.variance_serializer = H5ArraySerializer('variance', self.full_check, self.rank, self.n_workers)
		self.difftime_serializer = H5ArraySerializer('difftime', self.full_check, self.rank, self.n_workers)
		self.indices_serializer = H5ArraySerializer('indices', self.full_check, self.rank, self.n_workers)
		self.variance_serializer.init_chunks(h5dir.create_group('variance'), data.variance)
		self.difftime_serializer.init_chunks(h5dir.create_group('difftime'), data.difftime)
		self.indices_serializer.init_chunks(h5dir.create_group('indices'), data.indices)

	def write_chunk(self, h5dir: H5Dir, data: SLVBatch):
	 	# Leading edge overlaps are handled by simply not writing them.
		self.variance_serializer.write_chunk(h5dir['variance'], data.variance[data.overlap:])
		self.difftime_serializer.write_chunk(h5dir['difftime'], data.difftime[data.overlap:])
		self.indices_serializer.write_chunk(h5dir['indices'], data.indices[data.overlap:])

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return zip(
			self.variance_serializer.iter_chunks(h5dir['variance']),
			self.difftime_serializer.iter_chunks(h5dir['difftime']),
			self.indices_serializer.iter_chunks(h5dir['indices'])
		)

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.variance_serializer.read_chunks_info([in_dir['variance'] for in_dir in in_dirs])
		self.difftime_serializer.read_chunks_info([in_dir['difftime'] for in_dir in in_dirs])
		self.indices_serializer.read_chunks_info([in_dir['indices'] for in_dir in in_dirs])

	def init_serialize(self, out_dir: H5Dir):
		self.variance_serializer.init_serialize(out_dir)
		self.difftime_serializer.init_serialize(out_dir)
		self.indices_serializer.init_serialize(out_dir)

	def start_serialize(self) -> MultiIndex:
		i1 = self.variance_serializer.start_serialize()
		i2 = self.difftime_serializer.start_serialize()
		i3 = self.indices_serializer.start_serialize()
		return (i1, i2, i3)

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		(i1, i2, i3) = iat
		(variance, difftime, indices) = data
		i1 = self.variance_serializer.advance_serialize(out_dir['variance'], i1, variance)
		i2 = self.difftime_serializer.advance_serialize(out_dir['difftime'], i2, difftime)
		i3 = self.indices_serializer.advance_serialize(out_dir['indices'], i3, indices)
		return (i1, i2, i3)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		H5LVBatchSerializer.check(h5dir, full)
		assert h5dir['time'].shape[0] == h5dir['difftime'].shape[0]
		assert h5dir['data'].shape == h5dir['variance'].shape
		assert h5dir['data'].shape[0] == h5dir['indices'].shape[0]

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, with_indices=True) -> SLVBatch:
		lvb = H5LVBatchSerializer.load(h5dir, start, stop, overlap)
		return SLVBatch.from_lvb(
			lvb,
			H5ArraySerializer.load(h5dir['variance'], start, stop, overlap),
			H5ArraySerializer.load(h5dir['difftime'], start, stop, overlap),
			H5ArraySerializer.load(h5dir['indices'], start, stop, overlap) if with_indices else np.full(lvb.size, -1, dtype=np.int63)[:,np.newaxis]
		)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64], with_indices=True) -> SLVBatch:
		lvb = H5LVBatchSerializer.load_sparse(h5dir, indices)
		return SLVBatch.from_lvb(
			lvb,
			H5ArraySerializer.load_sparse(h5dir['variance'], indices),
			H5ArraySerializer.load_sparse(h5dir['difftime'], indices),
			H5ArraySerializer.load_sparse(h5dir['indices'], indices) if with_indices else np.full(lvb.size, -1, dtype=np.int64)[:,np.newaxis]
		)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None, with_indices=True) -> SLVBatch:
		lvb = H5LVBatchSerializer.load_multi(h5dirs, start, stop, overlap, time_offsets)
		return SLVBatch.from_lvb(
			lvb,
			H5ArraySerializer.load_multi([h5dir['variance'] for h5dir in h5dirs], start, stop, overlap),
			H5ArraySerializer.load_multi([h5dir['difftime'] for h5dir in h5dirs], start, stop, overlap),
			H5ArraySerializer.load_multi([h5dir['indices'] for h5dir in h5dirs], start, stop, overlap) if with_indices else np.full(lvb.size, -1, dtype=np.int64)[:,np.newaxis]
		)

'''
Loading SLVBatch from SLLVBatch (primarily for GUI)
- This does not load the indices
'''

class H5SLVBatchSerializer_GUI(H5SLVBatchSerializer):

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return H5SLVBatchSerializer.get_size(h5dir['summary'])

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> SLVBatch:
		return H5SLVBatchSerializer.load(h5dir['summary'], start, stop, overlap, with_indices=False)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> SLVBatch:
		return H5SLVBatchSerializer.load_sparse(h5dir['summary'], indices, with_indices=False)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> SLVBatch:
		return H5SLVBatchSerializer.load_multi([h5dir['summary'] for h5dir in h5dirs], start, stop, overlap, time_offsets, with_indices=False)


