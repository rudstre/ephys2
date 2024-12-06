'''
Labeled vector batch
'''

from .vbatch import *

from ephys2.lib.sparse import *
from ephys2.lib.cluster import *
from ephys2.lib.array import mkshape


@dataclass
class LVBatch(VBatch):
	'''
	A single labeled vector stream
	Unlike LLVBatch, overlap is allowed to be arbitrary.
	'''
	labels: Labeling 							# Labels

	def append(self, other: 'LVBatch'):
		super().append(other)
		self.labels = np.concatenate((self.labels, other.labels[other.overlap:]))

	def split(self, idx: int) -> 'LVBatch':
		''' 
		Split `idx` from the leading edge. 
		'''
		vb = super().split(idx)
		self.labels, other_labels = self.labels[idx:], self.labels[:idx]
		return LVBatch.from_vb(vb, other_labels)

	@staticmethod
	def empty(ndim: int) -> 'LVBatch':
		return LVBatch.from_vb(VBatch.empty(ndim), np.empty((0,), dtype=np.int64))

	def copy(self) -> 'LVBatch':
		return LVBatch.from_vb(super().copy(), self.labels.copy())

	@staticmethod
	def random_generate(ndim: int, size: int, overlap: int=0, maxsize: int=100, labels: Optional[Labeling]=None) -> 'LVBatch':
		vb = VBatch.random_generate(ndim, size=size, overlap=overlap, maxsize=maxsize)
		if labels is None:
			nlabels = random.randint(1, size)
			labels = random_labeling(size, nlabels)
		return LVBatch.from_vb(vb, labels)

	def __eq__(self, other: 'LVBatch') -> bool:
		return super().__eq__(other) and np.allclose(self.labels, other.labels)

	def to_vb(self) -> VBatch:
		return VBatch(time=self.time, data=self.data, overlap=self.overlap)

	@staticmethod
	def from_vb(vb: VBatch, labels: Labeling) -> 'LVBatch':
		return LVBatch(time=vb.time, data=vb.data, overlap=vb.overlap, labels=labels)

	def __getitem__(self, idx: slice) -> 'LVBatch':
		vtime = self.time[idx]
		vdata = self.data[idx]
		vlabels = self.labels[idx]
		overlap = min(self.overlap, vtime.size)
		return LVBatch(time=vtime, data=vdata, labels=vlabels, overlap=overlap)

	@staticmethod
	def memory_estimate(N: int, M: int) -> int:
		return VBatch.memory_estimate(N, M) + np.dtype(np.int64).itemsize * N 

'''
Multiple labeled vector batches
'''

@dataclass
class LVMultiBatch(VMultiBatch):
	items: Dict[str, LVBatch]

	def split(self, idx: int) -> 'LVMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return LVMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'LVMultiBatch') -> 'LVMultiBatch':
		return LVMultiBatch(items={item_id: LVBatch.empty(item.ndim) for item_id, item in other.items.items()})

	def copy(self) -> 'LVMultiBatch':
		return LVMultiBatch(items={item_id: item.copy() for item_id, item in self.items.items()})

	@staticmethod
	def random_generate(nitems: int, ndim: int, size: int, overlap: int=0, maxsize: int=100, labels: Optional[Labeling]=None) -> 'LVMultiBatch':
		return LVMultiBatch(items={
			str(i): LVBatch.random_generate(ndim, size, overlap=overlap, maxsize=maxsize, labels=labels) for i in range(nitems)
		})

	def to_vmb(self) -> VMultiBatch:
		return VMultiBatch(items={item_id: item.to_vb() for item_id, item in self.items.items()})

	@staticmethod
	def memory_estimate(nitems: int, N: int, M: int) -> int:
		return nitems * LVBatch.memory_estimate(N, M)


