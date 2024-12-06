'''
HDF5 serializer for time batch.
'''

from typing import Optional
import pdb

from .base import *
from .array import *

from ephys2.lib.types.tbatch import *

class H5TBatchSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return TBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['time']

	def init_chunks(self, h5dir: H5Dir, data: TBatch):
		self.time_serializer = H5ArraySerializer('time', self.full_check, self.rank, self.n_workers)
		self.time_serializer.init_chunks(h5dir.create_group('time'), data.time)

	def write_chunk(self, h5dir: H5Dir, data: TBatch):
		self.time_serializer.write_chunk(h5dir['time'], data.time[data.overlap:]) # Leading edge overlaps are handled by simply not writing them.

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return self.time_serializer.iter_chunks(h5dir['time'])

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.time_serializer.read_chunks_info([in_dir['time'] for in_dir in in_dirs])

	def init_serialize(self, out_dir: H5Dir):
		self.time_serializer.init_serialize(out_dir)

	def start_serialize(self) -> MultiIndex:
		return self.time_serializer.start_serialize()

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		return self.time_serializer.advance_serialize(out_dir['time'], iat, data)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		H5ArraySerializer.check(h5dir['time'], full)

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> TBatch:
		overlap = 0 if (start is None or start == 0) else overlap
		vtime = H5ArraySerializer.load(h5dir['time'], start, stop, overlap)
		overlap = min(vtime.size, overlap)
		return TBatch(time=vtime, overlap=overlap)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> TBatch:
		vtime = H5ArraySerializer.load_sparse(h5dir['time'], indices)
		return TBatch(time=vtime, overlap=0)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> TBatch:
		overlap = 0 if (start is None or start == 0) else overlap
		vtime = H5ArraySerializer.load_multi([h5dir['time'] for h5dir in h5dirs], start, stop, overlap, offsets=time_offsets)
		overlap = min(vtime.size, overlap)
		return TBatch(time=vtime, overlap=overlap)


'''
Multiple batches
'''

class H5TMultiBatchSerializer(H5MultiSerializer):

	@classmethod
	def data_type(cls: type) -> str:
		return TMultiBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def item_serializer(cls: type) -> type:
		return H5TBatchSerializer
