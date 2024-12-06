'''
Times batch 
'''

from typing import Optional
import numpy as np 
import numpy.typing as npt
from dataclasses import dataclass

from .tbatch import *

from ephys2.lib.cluster import *

'''
A batch data structure containing a labeled sequence of temporal events.
Example: firing times for distinct neurons.
'''

@dataclass
class LTBatch(TBatch):
	labels: Labeling 							# Labels

	def append(self, other: 'LTBatch'):
		super().append(other)
		self.labels = np.concatenate((self.labels, other.labels[other.overlap:]))

	def split(self, idx: int) -> 'LTBatch':
		self.time, other_time = self.time[idx:], self.time[:idx]
		self.labels, other_label = self.labels[idx:], self.labels[:idx]
		self.overlap, other_overlap = max(0, self.overlap - idx), min(idx, self.overlap)
		return LTBatch(
			time = other_time, 
			labels = other_label, 
			overlap = other_overlap
		)

	@staticmethod
	def empty() -> 'LTBatch':
		return LTBatch(
			time = np.empty((0,), dtype=np.int64),
			labels = np.empty((0,), dtype=np.int64),
			overlap = 0
		)

	def copy(self) -> 'LTBatch':
		return LTBatch(
			time = self.time.copy(), 
			labels = self.labels.copy(), 
			overlap = self.overlap
		)

	@staticmethod
	def random_generate(size: Optional[int]=None, overlap: int=0, maxsize: int=100) -> 'LTBatch':
		if size is None:
			size = random.randint(overlap+1, maxsize)
		K = random.randint(1, size)
		return LTBatch(
			time = np.cumsum(np.random.randint(0, size, size=size)),
			labels = random_labeling(size, K),
			overlap = overlap
		)

	def __eq__(self, other: 'LTBatch') -> bool:
		'''
		Equality doesn't check for overlap, only of the underlying data.
		'''
		return (
			np.allclose(self.time, other.time) and 
			np.allclose(self.labels, other.labels)
		)

	@staticmethod
	def memory_estimate(N: int) -> int:
		return N * np.dtype(np.int64).itemsize * 2

'''
Multiple time batches
'''

@dataclass
class LTMultiBatch(TMultiBatch):
	items: Dict[str, LTBatch]

	def split(self, idx: int) -> 'LTMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return LTMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'LTMultiBatch') -> 'LTMultiBatch':
		return LTMultiBatch(items={item_id: LTBatch.empty() for item_id, item in other.items.items()})

	def copy(self) -> 'LTMultiBatch':
		return LTMultiBatch(items={item_id: item.copy() for item_id, item in self.items.items()})

	@staticmethod
	def random_generate(nitems: int, size: Optional[int]=None, overlap: int=0, maxsize: int=100) -> 'LTMultiBatch':
		return LTMultiBatch(items={
			str(i): LTBatch.random_generate(size=size, overlap=overlap, maxsize=maxsize) for i in range(nitems)
		})

	@staticmethod
	def memory_estimate(nitems: int, N: int) -> int:
		return nitems * LTBatch.memory_estimate(N)
