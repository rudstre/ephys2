'''
Signal batch
'''

from .vbatch import *


'''
A batch data structure whose samples are signals; indexed uniformly in time with a sampling rate.
'''

@dataclass
class SBatch(VBatch):
	fs: int # Sampling rate

	def split(self, idx: int) -> 'SBatch':
		return SBatch.from_vb(super().split(idx), self.fs)

	@staticmethod
	def empty(ndim: int, fs: int=1) -> 'SBatch':
		return SBatch.from_vb(VBatch.empty(ndim), fs)

	def copy(self) -> 'SBatch':
		return SBatch.from_vb(super().copy(), fs=self.fs)

	@staticmethod
	def random_generate(ndim: int, size: Optional[int]=None, overlap: int=0, maxsize: int=1000, fs=1) -> 'SBatch':
		return SBatch.from_vb(
			VBatch.random_generate(ndim, size=size, overlap=overlap, maxsize=maxsize),
			fs
		)

	def __eq__(self, other: 'SBatch') -> bool:
		return super().__eq__(other) and self.fs == other.fs

	@staticmethod
	def from_vb(vb: VBatch, fs: int) -> 'SBatch':
		return SBatch(time=vb.time, data=vb.data, overlap=vb.overlap, fs=fs)



'''
Multiple signal batches
'''

@dataclass
class SMultiBatch(VMultiBatch):
	items: Dict[str, SBatch]

	def split(self, idx: int) -> 'SMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return SMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'SMultiBatch') -> 'SMultiBatch':
		return SMultiBatch(items={item_id: SBatch.empty(item).ndim for item_id, item in other.items.items()})

	def copy(self) -> 'SMultiBatch':
		return SMultiBatch(items={item_id: item.copy() for item_id, item in other.items.items()})

	@staticmethod
	def random_generate(nitems: int, ndim: int, size: Optional[int]=None, overlap: int=0, maxsize: int=1000, fs=1) -> 'SMultiBatch':
		return VMultiBatch(items={
			str(i): SBatch.random_generate(ndim, size=size, overlap=overlap, maxsize=maxsize, fs=fs) for i in range(nitems)
		})



