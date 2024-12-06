'''
Base data structures 
See the documentation in PROJECT_ROOT/data.md
'''

from typing import Dict, List, Callable, Any, Union, NewType, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
import numpy.typing as npt
import scipy.sparse as sp
import random

from ephys2.lib.array import mkshape

'''
Base data structure representing a batch of structured samples (need not be vector-like).
Implements a basic algebra of operations, including splitting and merging.
'''

class Batch(ABC):
	''' 
	Base batch data structure
	'''

	@abstractmethod
	def append(self, other: 'Batch'):
		'''
		Append another batch, following in time.
		'''
		pass

	@abstractmethod
	def split(self, idx: int) -> 'Batch':
		'''
		Split data at index `idx` from the temporal leading edge.
		'''
		pass

	@abstractmethod
	def copy(self) -> 'Batch':
		'''
		Produce an independent copy.
		'''
		pass

	@abstractmethod
	def __eq__(self, other: 'Batch') -> bool:
		'''
		Check if the two batches are equal up to machine precision.
		'''
		pass

	@staticmethod
	@abstractmethod
	def empty() -> 'Batch':
		'''
		Produce an empty instance of the batch.
		'''
		pass

	@staticmethod
	@abstractmethod
	def random_generate(self) -> 'Batch':
		'''
		Generate a randomized instance, for testing purposes.
		'''
		pass

	@staticmethod
	@abstractmethod
	def memory_estimate() -> int:
		'''
		Estimated memory usage in bytes.
		'''
		pass

'''
A container for multiple batches supporting the same operations.
'''
@dataclass
class MultiBatch(Batch):
	# Batches 
	items: Dict[str, Batch]

	def __getitem__(self, item_id: str) -> Batch:
		return self.items[item_id]

	def __setitem__(self, item_id: str, item: Batch):
		self.items[item_id] = item

	def __eq__(self, other: 'MultiBatch') -> bool:
		is_eq = self.items.keys() == other.items.keys()
		if is_eq:
			for item_id, item in self.items.items():
				is_eq &= item == other.items[item_id]
		return is_eq

