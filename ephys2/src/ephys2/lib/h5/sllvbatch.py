'''
HDF5 serializer for summarized linked labeled vector batch.
'''
import pdb

from ephys2.lib.settings import global_settings

from .vbatch import *
from .llvbatch import *
from .slvbatch import *

from ephys2.lib.types.sllvbatch import *
from ephys2 import _cpp

class H5SLLVBatchSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return SLLVBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['summary']

	@classmethod
	def parent(cls: type) -> type:
		return H5LLVBatchSerializer

	def init_chunks(self, h5dir: H5Dir, data: SLLVBatch):
		self.summary_serializer = H5SLVBatchSerializer(self.full_check, self.rank, self.n_workers)
		self.summary_serializer.init_chunks_passthrough(h5dir.create_group('summary'), None, data.summary)

	def write_chunk(self, h5dir: H5Dir, data: SLLVBatch):
		self.summary_serializer.write_chunk_passthrough(h5dir['summary'], data.summary)

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return self.summary_serializer.iter_chunks_passthrough(h5dir['summary'])

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.summary_serializer.read_chunks_info_passthrough([in_dir['summary'] for in_dir in in_dirs])

	def init_serialize(self, out_dir: H5Dir):
		self.summary_serializer.init_serialize_passthrough(create_overwrite_group(out_dir, 'summary'))

	def start_serialize(self) -> MultiIndex:
		return self.summary_serializer.start_serialize_passthrough()

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, summary: MultiData) -> MultiIndex:
		return self.summary_serializer.advance_serialize_passthrough(out_dir['summary'], iat, summary)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		super(H5SLLVBatchSerializer, cls).check(h5dir, full)
		H5SLVBatchSerializer.check(h5dir['summary'], full)
		if full:
			lb1 = np.unique(h5dir['labels'])
			lb2 = np.unique(h5dir['summary']['labels'])
			assert np.allclose(lb1, lb2)

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	'''
	Note for loader methods:

	There is a one-way index correspondence from the summary to the LLVBatch.
	However, we don't incur the cost of sparse-loading the LLVBatch by default, so the summarized information is not loaded.
	This loader is intended to be used only for checkpointing.
	'''

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> LLVBatch:
		return H5LLVBatchSerializer.load(h5dir, start, stop, overlap)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> LLVBatch:
		return H5LLVBatchSerializer.load_sparse(h5dir, indices)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> LLVBatch:
		return H5LLVBatchSerializer.load_multi(h5dirs, start, stop, overlap, time_offsets)

	'''
	Split functions
	'''

	@classmethod
	def split_1d(cls: type, 
			h5dir: H5Dir, 
			label: np.int64, 
			index: np.int64, 
			linkage: Optional[EVIncidence]=None
		) -> Tuple[EVIncidence, LabelMap]:
		'''
		Split the data along the time axis by re-labeling and re-linking as necessary.
		'''
		B = int(h5dir.attrs['block_size'])

		# Get fine-grained indices to re-label
		labels_after = h5dir['summary']['labels'][index:index+B]
		indices_after = np.arange(index, index + labels_after.size, dtype=np.int64)
		indices_after = _cpp.filter_by_cc(label, linkage.tuple(), labels_after, indices_after)
		fine_indices = h5dir['summary']['indices'][indices_after].ravel()
		fine_indices = fine_indices[fine_indices > -1]
		assert fine_indices.size > 0, 'No fine-grained split indices found for split.'
		fine_index = fine_indices.min() # Get the minimum over all fine-grained indices, since they are out of order in the summarization
		
		# Get the fine-grained indices to preserve (for the summarization to remain consistent)
		labels_before = h5dir['summary']['labels'][max(0, index-B):index]
		indices_before = np.arange(max(0, index-B), index, dtype=np.int64)
		indices_before = _cpp.filter_by_cc(label, linkage.tuple(), labels_before, indices_before)
		preserved_fine_indices = set(np.unique(h5dir['summary']['indices'][indices_before].ravel()))
		
		# Perform the fine-grained split
		linkage, label_map = H5LLVBatchSerializer.split_1d(h5dir, label, fine_index, linkage, preserved_fine_indices)
		
		# Re-label & store the summarized labels
		_cpp.relabel(labels_after, label_map)
		h5dir['summary']['labels'][index:index + labels_after.size] = labels_after
		
		return linkage, label_map

	@classmethod
	def split_2d(cls: type, 
			h5dir: H5Dir, 
			label: np.int64, 
			indices: npt.NDArray[np.int64], 
			linkage: Optional[EVIncidence]=None
		) -> Tuple[EVIncidence, LabelMap]:
		'''
		Split the data at arbitrary indices according to an inclusion/exclusion criterion.
		'''
		# Degenerate case
		if indices.size == 0:
			return linkage
			
		# Get the fine-grained split indices & window
		indices.sort()
		fine_indices = h5dir['summary']['indices'][indices].ravel()
		fine_indices = fine_indices[fine_indices > -1]
		assert fine_indices.size > 0, 'No fine-grained split indices found.'
		if global_settings.debug_on:
			fidx_min = fine_indices.min()
			fidx_max = fine_indices.max()
			nblocks = (fidx_max - fidx_min) // int(h5dir.attrs['block_size']) + 1
			assert len(label_map) <= nblocks

		# Perform the fine-grained split
		linkage, label_map = H5LLVBatchSerializer.split_2d(h5dir, label, fine_indices, linkage)
		
		# Load the labels that need to be re-labeled
		labels = h5dir['summary']['labels'][indices]
		
		# Re-label & store the summarized labels
		_cpp.relabel(labels, label_map)
		h5dir['summary']['labels'][indices] = labels
		
		return linkage, label_map

'''
Multiple batches
'''

class H5SLLVMultiBatchSerializer(H5MultiSerializer):

	@classmethod
	def data_type(cls: type) -> str:
		return SLLVMultiBatch

	@classmethod
	def load_type(cls: type) -> type:
		'''
		Note for loader methods:

		There is a one-way index correspondence from the summary to the LLVBatch.
		However, we don't incur the cost of sparse-loading the LLVBatch by default, so the summarized information is not loaded.
		This loader is intended to be used only for checkpointing.
		'''
		return LLVMultiBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def item_serializer(cls: type) -> type:
		return H5SLLVBatchSerializer
