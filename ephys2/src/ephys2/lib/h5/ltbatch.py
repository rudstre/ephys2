'''
HDF5 serializer for time batch.
'''

from typing import Optional
import pdb

from .base import *
from .array import *
from .tbatch import *

from ephys2.lib.types.ltbatch import *

class H5LTBatchSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return LTBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['labels']

	@classmethod
	def parent(cls: type) -> type:
		return H5TBatchSerializer

	def init_chunks(self, h5dir: H5Dir, data: LTBatch):
		self.labels_serializer = H5ArraySerializer('labels', self.full_check, self.rank, self.n_workers)
		self.labels_serializer.init_chunks(h5dir.create_group('labels'), data.labels)

	def write_chunk(self, h5dir: H5Dir, data: LTBatch):
		# Leading edge overlaps are handled by simply not writing them.
		self.labels_serializer.write_chunk(h5dir['labels'], data.labels[data.overlap:])

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return self.labels_serializer.iter_chunks(h5dir['labels'])

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.labels_serializer.read_chunks_info([in_dir['labels'] for in_dir in in_dirs])

	def init_serialize(self, out_dir: H5Dir):
		self.labels_serializer.init_serialize(out_dir)

	def start_serialize(self) -> MultiIndex:
		return self.labels_serializer.start_serialize()

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, labels: MultiData) -> MultiIndex:
		return self.labels_serializer.advance_serialize(out_dir['labels'], iat, labels)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		H5ArraySerializer.check(h5dir['time'], full)
		H5ArraySerializer.check(h5dir['labels'], full)
		assert h5dir['time'].shape[0] == h5dir['labels'].shape[0]

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> LTBatch:
		overlap = 0 if (start is None or start == 0) else overlap
		vtime = H5ArraySerializer.load(h5dir['time'], start, stop, overlap)
		vlabels = H5ArraySerializer.load(h5dir['labels'], start, stop, overlap)
		overlap = min(vtime.size, overlap)
		return LTBatch(time=vtime, labels=vlabels, overlap=overlap)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> LTBatch:
		vtime = H5ArraySerializer.load_sparse(h5dir['time'], indices)
		vlabels = H5ArraySerializer.load_sparse(h5dir['labels'], indices)
		return LTBatch(time=vtime, labels=vlabels, overlap=0)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> LTBatch:
		overlap = 0 if (start is None or start == 0) else overlap
		vtime = H5ArraySerializer.load_multi([h5dir['time'] for h5dir in h5dirs], start, stop, overlap, offsets=time_offsets)
		vlabels = H5ArraySerializer.load_multi([h5dir['labels'] for h5dir in h5dirs], start, stop, overlap)
		overlap = min(vtime.size, overlap)
		return LTBatch(time=vtime, labels=vlabels, overlap=overlap)


'''
Multiple batches
'''

class H5LTMultiBatchSerializer(H5MultiSerializer):

	@classmethod
	def data_type(cls: type) -> str:
		return LTMultiBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def item_serializer(cls: type) -> type:
		return H5LTBatchSerializer
