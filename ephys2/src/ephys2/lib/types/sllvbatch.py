'''
Summarized linked & labeled vector batch
'''
import numpy as np
import numpy.typing as npt

from .llvbatch import *
from .slvbatch import *

@dataclass
class SLLVBatch(LLVBatch):
	'''
	Block-summarized version of LLVBatch
	'''
	summary: SLVBatch

	def append(self, other: 'SLLVBatch'):
		'''
		In the overlapping region this step chains links in the intersection together.
		'''
		super().append(other)
		self.summary.append(other.summary)

	def split(self, idx: int) -> 'SLLVBatch':
		''' 
		Split `idx` from the leading edge. 
		'''
		llvb = super().split(idx)
		summary = self.summary.split(idx)
		return SLLVBatch.from_llvb(llvb, summary)

	@staticmethod
	def empty(ndim: int, block_size: int, ndiffs: int, nindices: int) -> 'SLLVBatch':
		return SLLVBatch.from_llvb(LLVBatch.empty(ndim, block_size), SLVBatch.empty(ndim, ndiffs, nindices))

	def copy(self) -> 'SLLVBatch':
		return SLLVBatch.from_llvb(super().copy(), self.summary.copy())

	@staticmethod
	def random_generate(ndim: int, size: int, block_size: int, nlabels: int, ndiffs: int, nindices: int, overlap: int=0, maxsize: int=100, linkage: Optional[EVIncidence]=None) -> 'SLLVBatch':
		llvb = LLVBatch.random_generate(ndim, size, block_size, nlabels, overlap=overlap, maxsize=maxsize, linkage=linkage)
		summary = SLVBatch.random_generate(ndim, size, ndiffs, nindices, overlap=0, maxsize=maxsize)
		summary.labels = llvb.labels # Ensure consistency
		summary = summary[overlap:] # Ensure consistency
		return SLLVBatch.from_llvb(llvb, summary)

	def __eq__(self, other: 'SLLVBatch') -> bool:
		return super().__eq__(other) and (self.summary == other.summary)

	@staticmethod
	def from_llvb(llvb: LLVBatch, summary: SLVBatch) -> 'SLLVBatch':
		return SLLVBatch(time=llvb.time, data=llvb.data, overlap=llvb.overlap, labels=llvb.labels, linkage=llvb.linkage, block_size=llvb.block_size, full_links=llvb.full_links, summary=summary)

	def to_llvb(self) -> LLVBatch:
		return LLVBatch(time=self.time, data=self.data, overlap=self.overlap, labels=self.labels, linkage=self.linkage, block_size=self.block_size, full_links=self.full_links)

	@staticmethod
	def memory_estimate(N: int, M: int, ndiffs: int=10, R: int=1000, LR: int=10) -> int:
		# R is the estimated compression rate of the summary
		return SLVBatch.memory_estimate(N, M, ndiffs, R) + LLVBatch.memory_estimate(N, M, LR)

'''
Multiple summarized labeled vector batches
'''

@dataclass
class SLLVMultiBatch(LLVMultiBatch):
	items: Dict[str, SLLVBatch]

	def split(self, idx: int) -> 'SLLVMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return SLLVMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'SLLVMultiBatch') -> 'SLLVMultiBatch':
		return SLLVMultiBatch(items={item_id: SLLVBatch.empty(item.ndim, item.block_size, item.summary.ndiffs, item.summary.nindices) for item_id, item in other.items.items()})

	def copy(self) -> 'SLLVMultiBatch':
		return SLLVMultiBatch(items={item_id: item.copy() for item_id, item in self.items.items()})

	@staticmethod
	def random_generate(nitems: int, ndim: int, size: int, block_size: int, nlabels: int, ndiffs: int, nindices: int, overlap: int=0, maxsize: int=100, linkage: Optional[EVIncidence]=None) -> 'SLLVMultiBatch':
		return SLLVMultiBatch(items={
			str(i): SLLVBatch.random_generate(ndim, size, block_size, nlabels, ndiffs, nindices, overlap=overlap, maxsize=maxsize, linkage=linkage) for i in range(nitems)
		})

	def to_llvmb(self) -> LLVMultiBatch:
		return LLVMultiBatch(items={item_id: item.to_llvb() for item_id, item in self.items.items()})

	@staticmethod
	def memory_estimate(nitems: int, N: int, M: int, ndiffs: int=10, R: int=1000, LR: int=10) -> int:
		return nitems * SLLVBatch.memory_estimate(N, M, ndiffs, R, LR)

