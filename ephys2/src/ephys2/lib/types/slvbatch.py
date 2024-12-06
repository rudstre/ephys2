'''
Summarized & labeled vector batch
'''
import numpy as np
import numpy.typing as npt

from .lvbatch import *

@dataclass
class SLVBatch(LVBatch):
	'''
	Summarized version of LVBatch
	- time: summarized times from a cluster
	- data: summarized data from a cluster
	- labels: label of a cluster
	- variance: variance of data within a cluster
	- difftime: sub-sampled time difference (ISI) distribution within a cluster
	- indices: reverse-lookup of indices in the original LVBatch (convention is to use -1 nonexistent data; will have a fixed shape given by downsample_ratio)
	'''
	variance: npt.NDArray[np.float32]
	difftime: npt.NDArray[np.int64]
	indices: npt.NDArray[np.int64]

	@property
	def ndiffs(self) -> int:
		'''
		Number of diffs stored in difftime
		'''
		return self.difftime.shape[1] if len(self.difftime.shape) == 2 else 1

	@property
	def nindices(self) -> int:
		'''
		Number of indices stored 
		'''
		return self.indices.shape[1] if len(self.indices.shape) == 2 else 1

	def append(self, other: 'SLVBatch'):
		super().append(other)
		self.variance = np.concatenate((self.variance, other.variance[other.overlap:]))
		self.difftime = np.concatenate((self.difftime, other.difftime[other.overlap:]), axis=0)
		self.indices = np.concatenate((self.indices, other.indices[other.overlap:]))

	def split(self, idx: int) -> 'SLVBatch':
		''' 
		Split `idx` from the leading edge. 
		'''
		lvb = super().split(idx)
		self.variance, other_variance = self.variance[idx:], self.variance[:idx]
		self.difftime, other_difftime = self.difftime[idx:], self.difftime[:idx]
		self.indices, other_indices = self.indices[idx:], self.indices[:idx]
		return SLVBatch.from_lvb(vb, other_variance, other_difftime, other_indices)

	@staticmethod
	def empty(ndim: int, ndiffs: int, nindices: int) -> 'SLVBatch':
		variance = np.empty(mkshape(0, ndim), dtype=np.float32)
		difftime = np.empty(mkshape(0, ndiffs), dtype=np.int64)
		indices = np.empty(mkshape(0, nindices), dtype=np.int64)
		return SLVBatch.from_lvb(LVBatch.empty(ndim), variance, difftime, indices)

	def copy(self) -> 'SLVBatch':
		return SLVBatch.from_lvb(super().copy(), self.variance.copy(), self.difftime.copy(), self.indices.copy())

	@staticmethod
	def random_generate(ndim: int, size: int, ndiffs: int, nindices: int, overlap: int=0, maxsize: int=100, labels: Optional[Labeling]=None) -> 'SLVBatch':
		lvb = LVBatch.random_generate(ndim, size, overlap=overlap, maxsize=maxsize, labels=labels)
		variance = np.random.randn(*mkshape(size, ndim)).astype(np.float32)
		difftime = np.random.randint(0, 1000, size=mkshape(size, ndiffs), dtype=np.int64)
		indices = np.random.randint(0, size, size=mkshape(size, nindices), dtype=np.int64)
		return SLVBatch.from_lvb(lvb, variance, difftime, indices)

	def __eq__(self, other: 'SLVBatch') -> bool:
		return (
			super().__eq__(other) and 
			np.allclose(self.variance, other.variance) and
			np.allclose(self.difftime, other.difftime) and 
			np.allclose(self.indices, other.indices)
		)

	@staticmethod
	def from_lvb(lvb: LVBatch, variance: npt.NDArray[np.float32], difftime: npt.NDArray[np.int64], indices: npt.NDArray[np.int64]) -> 'SLVBatch':
		return SLVBatch(time=lvb.time, data=lvb.data, overlap=lvb.overlap, labels=lvb.labels, variance=variance, difftime=difftime, indices=indices)

	def __getitem__(self, idx: slice) -> 'SLVBatch':
		vtime = self.time[idx]
		vdata = self.data[idx]
		vlabels = self.labels[idx]
		vvariance = self.variance[idx]
		vdifftime = self.difftime[idx]
		vindices = self.indices[idx]
		overlap = min(self.overlap, vtime.size)
		return SLVBatch(time=vtime, data=vdata, labels=vlabels, variance=vvariance, difftime=vdifftime, indices=vindices, overlap=overlap)

	@staticmethod
	def memory_estimate(N: int, M: int, ndiffs: int=10, R: int=1000) -> int:
		# R is the estimated compression rate of the summary
		return LVBatch.memory_estimate(N, M) + int((1 / R) * (
			LVBatch.memory_estimate(N, M) + 
			N * M * np.dtype(np.float32).itemsize + 
			N * ndiffs * np.dtype(np.int64).itemsize + 
			N * R * np.dtype(np.int64).itemsize
		))

