'''
Vector batch
'''

import numpy as np
import numpy.typing as npt
from dataclasses import dataclass

from .batch import *
from ephys2.lib.array import mkshape


'''
A batch data structure whose samples are vectors; indexed by time.
'''

@dataclass
class VBatch(Batch):
	'''
	Batch data structure with time-indexed vector structure.
	'''
	time: npt.NDArray[np.int64]			# Time index (N,)
	data: npt.NDArray[np.float32]		# Data (N,M)
	overlap: int 										# Leading-edge overlap

	@property
	def ndim(self) -> int:
		''' 
		Get dimension (number of features) of each element in the batch; must be uniform.
		'''
		return 1 if len(self.data.shape) == 1 else self.data.shape[1]

	@property
	def size(self) -> int:
		''' 
		Get the size of the batch.
		'''
		return self.time.size

	def append(self, other: 'VBatch'):
		'''
		Append other time and data, accounting for overlap.
		'''
		self.time = np.concatenate((self.time, other.time[other.overlap:]))
		self.data = np.concatenate((self.data, other.data[other.overlap:]), axis=0)

	def split(self, idx: int) -> 'VBatch':
		'''
		Split from the leading edge, accounting for leading-edge overlap.
		'''
		self.time, other_time = self.time[idx:], self.time[:idx]
		self.data, other_data = self.data[idx:], self.data[:idx]
		self.overlap, other_overlap = max(0, self.overlap - idx), min(idx, self.overlap)
		return VBatch(time=other_time, data=other_data, overlap=other_overlap)

	@staticmethod
	def empty(ndim: int) -> 'VBatch':
		return VBatch(
			time = np.empty((0,), dtype=np.int64),
			data = np.empty(mkshape(0, ndim), dtype=np.int32),
			overlap = 0
		)

	def copy(self) -> 'VBatch':
		return VBatch(time=self.time.copy(), data=self.data.copy(), overlap=self.overlap)

	@staticmethod
	def random_generate(ndim: int, size: Optional[int]=None, overlap: int=0, maxsize: int=100) -> 'VBatch':
		if size is None:
			size = random.randint(overlap, maxsize)
		return VBatch(
			time = random.randint(0, 100) + np.arange(size, dtype=np.int64),
			data = np.random.randn(*mkshape(size, ndim)).astype(np.float32),
			overlap = overlap
		)

	def __eq__(self, other: 'VBatch') -> bool:
		'''
		Equality doesn't check for overlap, only of the underlying data.
		'''
		return (
			np.allclose(self.time, other.time) and
			np.allclose(self.data, other.data) 
		)

	def remove_overlap(self):
		'''
		Delete data from the leading-edge overlap
		'''
		if self.overlap > 0:
			self.split(self.overlap)

	def __getitem__(self, idx: slice) -> 'VBatch':
		vtime = self.time[idx]
		vdata = self.data[idx]
		overlap = min(self.overlap, vtime.size)
		return VBatch(time=vtime, data=vdata, overlap=overlap)

	@staticmethod
	def memory_estimate(N: int, M: int) -> int:
		return N * (
			(M * np.dtype(np.float32).itemsize) + 
			np.dtype(np.int64).itemsize
		)

'''
Multiple vector batches
'''


@dataclass
class VMultiBatch(MultiBatch):
	items: Dict[str, VBatch]

	def append(self, other: 'VMultiBatch'):
		for item_id, item in other.items.items():
			self.items[item_id].append(item)

	def split(self, idx: int) -> 'VMultiBatch':
		other_items = dict()
		for item_id in self.items:
			other_items[item_id] = self.items[item_id].split(idx)
		return VMultiBatch(items=other_items)

	@staticmethod
	def empty(other: 'VMultiBatch') -> 'VMultiBatch':
		return VMultiBatch(items={item_id: VBatch.empty(item.ndim) for item_id, item in other.items.items()})

	def copy(self) -> 'VMultiBatch':
		return VMultiBatch(items={item_id: item.copy() for item_id, item in self.items.items()})

	@staticmethod
	def random_generate(nitems: int, ndim: int, size: Optional[int]=None, overlap: int=0, maxsize: int=100) -> 'VMultiBatch':
		return VMultiBatch(items={
			str(i): VBatch.random_generate(ndim, size=size, overlap=overlap, maxsize=maxsize) for i in range(nitems)
		})

	def remove_overlap(self):
		for item in self.items.values():
			item.remove_overlap()

	@staticmethod
	def memory_estimate(nitems: int, N: int, M: int) -> int:
		return nitems * VBatch.memory_estimate(N, M)


