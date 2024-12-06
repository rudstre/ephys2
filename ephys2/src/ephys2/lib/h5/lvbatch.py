'''
HDF5 serializer for labeled vector batch.
'''

from .array import *
from .vbatch import *

from ephys2.lib.types.lvbatch import *

class H5LVBatchSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return LVBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['labels']

	@classmethod
	def parent(cls: type) -> type:
		return H5VBatchSerializer
	
	def init_chunks(self, h5dir: H5Dir, data: LVBatch):
		self.labels_serializer = H5ArraySerializer('labels', self.full_check, self.rank, self.n_workers)
		self.labels_serializer.init_chunks(h5dir.create_group('labels'), data.labels)

	def write_chunk(self, h5dir: H5Dir, data: LVBatch):
		self.labels_serializer.write_chunk(h5dir['labels'], data.labels[data.overlap:]) # Leading edge overlaps are handled by simply not writing them.

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
		H5VBatchSerializer.check(h5dir, full)
		assert h5dir['time'].shape == h5dir['labels'].shape 

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> LVBatch:
		return LVBatch.from_vb(
			H5VBatchSerializer.load(h5dir, start, stop, overlap),
			H5ArraySerializer.load(h5dir['labels'], start, stop, overlap)
		)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> LVBatch:
		return LVBatch.from_vb(
			H5VBatchSerializer.load_sparse(h5dir, indices),
			H5ArraySerializer.load_sparse(h5dir['labels'], indices)
		)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> LVBatch:
		return LVBatch.from_vb(
			H5VBatchSerializer.load_multi(h5dirs, start, stop, overlap, time_offsets),
			H5ArraySerializer.load_multi([h5dir['labels'] for h5dir in h5dirs], start, stop, overlap)
		)
		
'''
Multiple batches
'''

class H5LVMultiBatchSerializer(H5MultiSerializer):

	@classmethod
	def data_type(cls: type) -> str:
		return LVMultiBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def item_serializer(cls: type) -> type:
		return H5LVBatchSerializer
