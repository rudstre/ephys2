'''
HDF5 serializer for vector batch.
'''

from typing import Optional
import pdb

from .base import *
from .array import *

from ephys2.lib.types.vbatch import *

class H5VBatchSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return VBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['time', 'data']

	def init_chunks(self, h5dir: H5Dir, data: VBatch):
		self.time_serializer = H5ArraySerializer('time', self.full_check, self.rank, self.n_workers)
		self.data_serializer = H5ArraySerializer('data', self.full_check, self.rank, self.n_workers)
		self.time_serializer.init_chunks(h5dir.create_group('time'), data.time)
		self.data_serializer.init_chunks(h5dir.create_group('data'), data.data)

	def write_chunk(self, h5dir: H5Dir, data: VBatch):
		self.time_serializer.write_chunk(h5dir['time'], data.time[data.overlap:]) # Leading edge overlaps are handled by simply not writing them.
		self.data_serializer.write_chunk(h5dir['data'], data.data[data.overlap:])

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return zip(
			self.time_serializer.iter_chunks(h5dir['time']),
			self.data_serializer.iter_chunks(h5dir['data'])
		)

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.time_serializer.read_chunks_info([in_dir['time'] for in_dir in in_dirs])
		self.data_serializer.read_chunks_info([in_dir['data'] for in_dir in in_dirs])

	def init_serialize(self, out_dir: H5Dir):
		self.time_serializer.init_serialize(out_dir)
		self.data_serializer.init_serialize(out_dir)

	def start_serialize(self) -> MultiIndex:
		i1 = self.time_serializer.start_serialize()
		i2 = self.data_serializer.start_serialize()
		return (i1, i2)

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		'''
		Enforces the overlap condition during re-serialization.
		'''
		(i1, i2) = iat
		(time, data) = data
		i1 = self.time_serializer.advance_serialize(out_dir['time'], i1, time)
		i2 = self.data_serializer.advance_serialize(out_dir['data'], i2, data)
		return (i1, i2)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		H5ArraySerializer.check(h5dir['time'], full)
		H5ArraySerializer.check(h5dir['data'], full)
		assert h5dir['time'].shape[0] == h5dir['data'].shape[0]

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def get_ndim(cls: type, h5dir: H5Dir) -> int:
		super(H5VBatchSerializer, cls).get_ndim(h5dir)
		return h5dir['data'].shape[1]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> VBatch:
		overlap = 0 if (start is None or start == 0) else overlap
		vtime = H5ArraySerializer.load(h5dir['time'], start, stop, overlap)
		vdata = H5ArraySerializer.load(h5dir['data'], start, stop, overlap)
		overlap = min(vtime.size, overlap)
		return VBatch(time=vtime, data=vdata, overlap=overlap)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> VBatch:
		vtime = H5ArraySerializer.load_sparse(h5dir['time'], indices)
		vdata = H5ArraySerializer.load_sparse(h5dir['data'], indices)
		return VBatch(time=vtime, data=vdata, overlap=0)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> VBatch:
		overlap = 0 if (start is None or start == 0) else overlap
		vtime = H5ArraySerializer.load_multi([h5dir['time'] for h5dir in h5dirs], start, stop, overlap, offsets=time_offsets)
		vdata = H5ArraySerializer.load_multi([h5dir['data'] for h5dir in h5dirs], start, stop, overlap)
		overlap = min(vtime.size, overlap)
		return VBatch(time=vtime, data=vdata, overlap=overlap)


'''
Multiple batches
'''

class H5VMultiBatchSerializer(H5MultiSerializer):

	@classmethod
	def data_type(cls: type) -> str:
		return VMultiBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def item_serializer(cls: type) -> type:
		return H5VBatchSerializer
