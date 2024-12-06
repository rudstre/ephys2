'''
Times batch 
'''

from typing import Optional
import numpy as np 
import numpy.typing as npt
from dataclasses import dataclass

from .batch import *

'''
A batch data structure containing a sequence of temporal events.
Example: firing times for a single neuron or digital pulse train.
'''

@dataclass
class TBatch(Batch):
	time: npt.NDArray[np.int64] 	# Time
	overlap: int

	@property
	def size(self) -> int:
		return self.time.size

	def append(self, other: 'TBatch'):
		self.time = np.concatenate((self.time, other.time[other.overlap:]))

	def split(self, idx: int) -> 'TBatch':
		self.time, other_time = self.time[idx:], self.time[:idx]
		self.overlap, other_overlap = max(0, self.overlap - idx), min(idx, self.overlap)
		return TBatch(
			time = other_time, 
			overlap = other_overlap
		)

	@staticmethod
	def empty() -> 'TBatch':
		return TBatch(
			time = np.empty((0,), dtype=np.int64),
			overlap = 0
		)

	def copy(self) -> 'TBatch':
		return TBatch(
			time = self.time.copy(), 
			overlap = self.overlap
		)

	@staticmethod
	def random_generate(size: Optional[int]=None, overlap: int=0, maxsize: int=100) -> 'TBatch':
		if size is None:
			size = random.randint(overlap+1, maxsize)
		return TBatch(
			time = np.cumsum(np.random.randint(0, size, size=size)),
			overlap = overlap
		)

	def __eq__(self, other: 'TBatch') -> bool:
		'''
		Equality doesn't check for overlap, only of the underlying data.
		'''
		return np.allclose(self.time, other.time)

	def remove_overlap(self):
		'''
		Delete data from the leading-edge overlap
		'''
		self.split(self.overlap)

	@staticmethod
	def memory_estimate(N: int) -> int:
		return N * np.dtype(np.int64).itemsize 

'''
Multiple time batches
'''

@dataclass
class TMultiBatch(MultiBatch):
	items: Dict[str, TBatch]

	def append(self, other: 'TMultiBatch'):
		for item_id, item in other.items.items():
			self.items[item_id].append(item)

	def split(self, idx: int) -> 'TMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return TMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'TMultiBatch') -> 'TMultiBatch':
		return TMultiBatch(items={item_id: TBatch.empty() for item_id, item in other.items.items()})

	def copy(self) -> 'TMultiBatch':
		return TMultiBatch(items={item_id: item.copy() for item_id, item in self.items.items()})

	@staticmethod
	def random_generate(nitems: int, size: Optional[int]=None, overlap: int=0, maxsize: int=100) -> 'TMultiBatch':
		return TMultiBatch(items={
			str(i): TBatch.random_generate(size=size, overlap=overlap, maxsize=maxsize) for i in range(nitems)
		})

	def remove_overlap(self):
		for item in self.items.values():
			item.remove_overlap()

	@staticmethod
	def memory_estimate(nitems: int, N: int) -> int:
		return nitems * TBatch.memory_estimate(N)
