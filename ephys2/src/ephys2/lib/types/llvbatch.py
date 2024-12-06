'''
Linked & labeled vector batch
'''

from .vbatch import *
from .lvbatch import LVBatch, LVMultiBatch

from ephys2.lib.sparse import *
from ephys2.lib.cluster import *
from ephys2.lib.array import mkshape

@dataclass
class LLVBatch(LVBatch):
	'''
	A single linked & labeled vector stream
	overlap: is measured in number of samples in self.data, but must subdivide self.block_size. 
	'''
	linkage: EVIncidence
	block_size: int # Block size in which labeling is done
	full_links: bool # Whether the links matrix is the entire graph or just the links between two adjacent blocks
	
	def append(self, other: 'LLVBatch'):
		'''
		The append operation takes the simple union of the two graphs, without regard for repeated edges.
		Thus, any overlapping data should not contain edges.
		full_links causes precedence of one graph over the other.
		'''
		super().append(other)
		if self.full_links:
			pass
		elif other.full_links:
			self.linkage = other.linkage
		else:
			self.linkage = ev_graph_union(self.linkage, other.linkage)

	def split(self, idx: int) -> 'LLVBatch':
		''' 
		The split operation does not modify the graph.
		'''
		lvb = super().split(idx)
		return LLVBatch.from_lvb(lvb, self.linkage.copy(), self.block_size, self.full_links)

	@staticmethod
	def empty(ndim: int, block_size: int) -> 'LLVBatch':
		return LLVBatch.from_lvb(LVBatch.empty(ndim), empty_ev_graph(), block_size, False)

	def copy(self) -> 'LLVBatch':
		return LLVBatch.from_lvb(super().copy(), self.linkage.copy(), self.block_size, self.full_links)

	@staticmethod
	def random_generate(ndim: int, size: int, block_size: int, nlabels: int, overlap: int=0, maxsize: int=100, nlinks: int=10, linkage: Optional[EVIncidence]=None) -> 'LLVBatch':
		lvb = LVBatch.random_generate(ndim, size=size, overlap=overlap, maxsize=maxsize)
		linkage = random_ev_graph(nlabels) if linkage is None else linkage
		return LLVBatch.from_lvb(lvb, linkage, block_size, False)

	def __eq__(self, other: 'LLVBatch') -> bool:
		return (
			super().__eq__(other) and 
			self.linkage == other.linkage and 
			self.block_size == other.block_size  
		)

	def __getitem__(self, idx: slice) -> 'LLVBatch':
		'''
		Like split(), __getitem__ does not modify the linkage.
		'''
		return LLVBatch.from_lvb(super().__getitem__(idx), self.linkage.copy(), self.block_size, self.full_links)

	def to_lvb(self) -> LVBatch:
		return LVBatch(time=self.time, data=self.data, labels=self.labels, overlap=self.overlap)

	@staticmethod
	def from_lvb(lvb: LVBatch, linkage: EVIncidence, block_size: int, full_links: bool) -> 'LLVBatch':
		return LLVBatch(time=lvb.time, data=lvb.data, overlap=lvb.overlap, labels=lvb.labels, linkage=linkage, block_size=block_size, full_links=full_links)

	@staticmethod
	def memory_estimate(N: int, M: int, LR: int=10) -> int:
		# LR is the estimated compression rate of the labeling
		return LVBatch.memory_estimate(N, M) + int(
			N * np.dtype(np.int64).itemsize + 
			2 * N * (1 / LR) * np.dtype(np.int64).itemsize + 
			2 * N * 2
		)

'''
Multiple labeled vector batches
'''

@dataclass
class LLVMultiBatch(LVMultiBatch):
	items: Dict[str, LLVBatch]

	def split(self, idx: int) -> 'LLVMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return LLVMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'LLVMultiBatch') -> 'LLVMultiBatch':
		return LLVMultiBatch(items={item_id: LLVBatch.empty(item.ndim, item.block_size) for item_id, item in other.items.items()})

	def copy(self) -> 'LLVMultiBatch':
		return LLVMultiBatch(items={item_id: item.copy() for item_id, item in self.items.items()})

	@staticmethod
	def random_generate(nitems: int, ndim: int, size: int, block_size: int, nlabels: int, overlap: int=0, nlinks: int=10, maxsize: int=100, linkage: Optional[EVIncidence]=None) -> 'LLVMultiBatch':
		return LLVMultiBatch(items={
			str(i): LLVBatch.random_generate(ndim, size, block_size, nlabels, overlap=overlap, nlinks=nlinks, maxsize=maxsize, linkage=linkage) for i in range(nitems)
		})

	def to_lvmb(self) -> LVMultiBatch:
		return LVMultiBatch(items={item_id: item.to_lvb() for item_id, item in self.items.items()})

	@staticmethod
	def memory_estimate(nitems: int, N: int, M: int, LR: int=10) -> int:
		# LR is the estimated compression rate of the labeling
		return nitems * LLVBatch.memory_estimate(N, M, LR)


