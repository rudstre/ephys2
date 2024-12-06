'''
HDF5 serializer for labeled vector batch.
'''

from .utils import *
from .array import *
from .sparse import *
from .lvbatch import *

from ephys2.lib.types.llvbatch import *
from ephys2.lib.graph import *
from ephys2 import _cpp

class H5LLVBatchSerializer(H5Serializer):
	memoized_links: Dict[H5ID, EVIncidence] = dict()

	@classmethod
	def data_type(cls: type) -> type:
		return LLVBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def fields(cls: type) -> List[str]:
		return ['labels', 'linkage']

	@classmethod
	def attrs(cls: type) -> List[str]:
		return ['block_size']

	@classmethod
	def parent(cls: type) -> type:
		return H5VBatchSerializer # The parent is VBatch rather than LVBatch, since the labels and links should be written in tandem

	def init_chunks(self, h5dir: H5Dir, data: LLVBatch):
		self.labels_serializer = H5ArraySerializer('labels', self.full_check, self.rank, self.n_workers)
		self.labels_serializer.init_chunks(h5dir.create_group('labels'), data.labels)
		self.linkage_serializer = H5CSRSerializer(self.full_check, self.rank, self.n_workers)
		self.linkage_serializer.init_chunks(h5dir.create_group('linkage'), data.linkage)
		self.block_size = h5dir.attrs['block_size'] = data.block_size
		self.full_links = data.full_links
		self.full_links_written = False

	def write_chunk(self, h5dir: H5Dir, data: LLVBatch):
		self.labels_serializer.write_chunk(h5dir['labels'], data.labels[data.overlap:]) # Leading edge overlaps are handled by simply not writing them.
		assert data.full_links == self.full_links, 'Inconsistency between full_links setting in successive batches'
		if (self.full_links and self.full_links_written):
			self.linkage_serializer.write_chunk(h5dir['linkage'], empty_ev_graph()) # Write an empty graph if the full links has already been written
		else:
			self.linkage_serializer.write_chunk(h5dir['linkage'], data.linkage)
			self.full_links_written = True

	def iter_chunks(self, h5dir: H5Dir) -> Gen[MultiData]:
		return zip(
			self.labels_serializer.iter_chunks(h5dir['labels']),
			self.linkage_serializer.iter_chunks(h5dir['linkage'])
		)

	def read_chunks_info(self, in_dirs: List[H5Dir]):
		self.labels_serializer.read_chunks_info([in_dir['labels'] for in_dir in in_dirs])
		self.linkage_serializer.read_chunks_info([in_dir['linkage'] for in_dir in in_dirs])

	def init_serialize(self, out_dir: H5Dir):
		self.labels_serializer.init_serialize(out_dir)
		self.linkage_serializer.init_serialize(create_overwrite_group(out_dir, 'linkage'))
		out_dir.attrs['block_size'] = self.block_size

	def start_serialize(self) -> MultiIndex:
		return (
			self.labels_serializer.start_serialize(),
			self.linkage_serializer.start_serialize()
		)

	def advance_serialize(self, out_dir: H5Dir, iat: MultiIndex, data: MultiData) -> MultiIndex:
		(i1, i2) = iat
		(labels, linkage) = data
		i1 = self.labels_serializer.advance_serialize(out_dir['labels'], i1, labels)
		i2 = self.linkage_serializer.advance_serialize(out_dir['linkage'], i2, linkage)
		return (i1, i2)

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		H5ArraySerializer.check(h5dir['labels'], full)
		assert h5dir['time'].shape == h5dir['labels'].shape 
		H5CSRSerializer.check(h5dir['linkage'], full)
		assert 'block_size' in h5dir.attrs
		assert h5dir['linkage'].attrs['shape'][1] in [0, h5dir['labels'].shape[0]] # Check consistency of the label space
		if full:
			# Check consistency of the edge-vertex incidence matrix
			indptr = h5dir['linkage']['indptr'][:]
			diffs = set(np.unique(np.diff(indptr)))
			assert diffs in [set(), {0}, {0, 2}, {2}]

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> LLVBatch:
		'''
		Note: this function will load the entire linkage matrix (memoized).
		'''
		return LLVBatch.from_lvb(
			H5LVBatchSerializer.load(h5dir, start, stop, overlap),
			cls.load_links(h5dir),
			h5dir.attrs['block_size'],
			full_links=True
		)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> LLVBatch:
		'''
		Note: this function will load the entire linkage matrix (memoized).
		'''
		return LLVBatch.from_lvb(
			H5LVBatchSerializer.load_sparse(h5dir, indices),
			cls.load_links(h5dir),
			h5dir.attrs['block_size'],
			full_links=True
		)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> LLVBatch:
		'''
		Note: this function will load the entire linkage matrix (memoized).
		'''
		assert all(h5dir.attrs['block_size'] == h5dirs[0].attrs['block_size'] for h5dir in h5dirs)
		return LLVBatch.from_lvb(
			H5LVBatchSerializer.load_multi(h5dirs, start, stop, overlap, time_offsets),
			cls.load_links_multi(h5dirs),
			h5dirs[0].attrs['block_size'],
			full_links=True
		)

	@classmethod
	def load_links(cls: type, h5dir: H5Dir) -> EVIncidence:
		'''
		Load the links matrix with memoization.
		'''
		li_id = h5dir_id(h5dir['linkage'])
		if li_id not in cls.memoized_links:
			cls.memoized_links[li_id] = H5CSRSerializer.load(h5dir['linkage'])
		return cls.memoized_links[li_id]

	@classmethod
	def load_links_multi(cls: type, h5dirs: List[H5Dir]) -> EVIncidence:
		return csr_concat([
			cls.load_links(h5dir) for h5dir in h5dirs
		])

	@classmethod
	def split_1d(cls: type, 
			h5dir: H5Dir, 
			label: np.int64,
			index: np.int64, 
			linkage: Optional[EVIncidence]=None,
			preserved_indices: Set[np.int64]=set()
		) -> Tuple[EVIncidence, LabelMap]:
		'''
		Split the data along the time axis by re-labeling and re-linking as necessary.
		'''
		# Find label space (start, end) for the block which is being split
		B = int(h5dir.attrs['block_size'])
		block_start = index - (index % B)
		block_end = block_start + B
		assert block_start <= index <= block_end

		# Load the labels & links and perform the split
		block_labels = h5dir['labels'][block_start:block_end]
		if linkage is None:
			linkage = H5CSRSerializer.load(h5dir['linkage'])
		label_map = _cpp.split_block_1d(
			block_labels,
			block_start, 
			block_end, 
			index,
			label,
			linkage.tuple(),
			preserved_indices
		)

		# Save the new labels & links
		h5dir['labels'][block_start:block_end] = block_labels
		H5CSRSerializer.replace(h5dir['linkage'], linkage)

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

		if linkage is None:
			linkage = H5CSRSerializer.load(h5dir['linkage'])
			
		# Find the blocks which are being split
		B = int(h5dir.attrs['block_size'])
		window_0 = indices.min()
		window_1 = indices.max()
		blocks_start = window_0 - (window_0 % B)
		blocks_end = window_1 - (window_1 % B) + B
		assert blocks_start <= window_0 < window_1 <= blocks_end

		# Load the labels and perform the split
		labels = h5dir['labels'][blocks_start:blocks_end]
		label_map = _cpp.split_blocks_2d(
			labels,
			blocks_start, 
			blocks_end,
			B,
			set(indices),
			label,
			linkage.tuple()
		)

		# Add links for the new labels
		linkage = add_links(linkage, list(set(label_map.values())))

		# Save the new labels & links
		h5dir['labels'][blocks_start:blocks_end] = labels
		H5CSRSerializer.replace(h5dir['linkage'], linkage)

		return linkage, label_map

'''
Multiple batches
'''

class H5LLVMultiBatchSerializer(H5MultiSerializer):

	@classmethod
	def data_type(cls: type) -> str:
		return LLVMultiBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def item_serializer(cls: type) -> type:
		return H5LLVBatchSerializer
