'''
NumPy array utilities
'''

from typing import List, Optional, Any, Tuple, Union
import numpy as np
import numpy.typing as npt
from scipy.linalg import block_diag

'''
Types
'''

Mask = Union[npt.NDArray[bool], slice]


'''
Functions
'''

def safe_hstack(arrs: List[npt.NDArray]):
	return np.array([]) if len(arrs) == 0 else np.hstack(arrs)

def safe_vstack(arrs: List[npt.NDArray]):
	return np.array([]) if len(arrs) == 0 else np.vstack(arrs)

def arange2d(arr1: npt.NDArray, arr2: npt.NDArray) -> npt.NDArray:
	'''
	TODO: C++ implementation
	'''
	assert arr1.shape == arr2.shape
	assert len(arr1.shape) == 1
	return np.hstack([
		np.arange(i, j) for i, j in zip(arr1, arr2)
	])

def intercalate(arr1: npt.NDArray, arr2: npt.NDArray) -> npt.NDArray:
	'''
	Interleave values of two arrays.
	https://stackoverflow.com/questions/5347065/interweaving-two-numpy-arrays
	'''
	return np.ravel(np.column_stack((arr1, arr2)))

def min_def(arr: npt.NDArray, default: Optional[Any]=0) -> Any:
	'''
	Length-safe minimum function.
	'''
	if arr.size == 0:
		return default
	return arr.min()

def max_def(arr: npt.NDArray, default: Optional[Any]=0) -> Any:
	'''
	Length-safe maximum function.
	'''
	if arr.size == 0:
		return default
	return arr.max()

def mkshape(N: int, M: int) -> Tuple[int, ...]:
	'''
	Constructs a squeezed shape representing a 1d or 2d array as appropriate.
	'''
	return (N,) if M == 1 else (N, M)

def random_mask(N: int, p: float) -> npt.NDArray[bool]:
	'''
	Construct a random mask of a range
	'''
	assert 0 <= p <= 1
	return np.random.uniform(low=0, high=1, size=N) <= p

def make_square(M: npt.NDArray, val: Any):
	'''
	Make a matrix square by padding.
	'''
	(a,b) = M.shape
	if a > b:
		padding=((0,0),(0,a-b))
	else:
		padding=((0,b-a),(0,0))
	return np.pad(M, padding, mode='constant', constant_values=val)

def square_block_diag(Xs: List[npt.NDArray]) -> npt.NDArray:
	'''
	Make a square block-diagonal matrix by padding with zeros.
	'''
	Xs = [make_square(X, 0) for X in Xs if X.size > 0] # scipy block_diag treats empty matrices strangely
	return block_diag(*Xs)

def combine_masks(m1: Mask, m2: Mask) -> Mask:
	'''
	Combine two masks on the same domain.
	'''
	if type(m1) is slice:
		return m2
	elif type(m2) is slice:
		return m1
	return np.logical_and(m1, m2)

def read_binary_array(path: str, dtype: np.dtype, shape: Tuple[int,int], offset: int) -> npt.NDArray:
	'''
	Read a binary array from a file (stored in row-major order)
	'''
	M = 1 if len(shape) == 1 else shape[1]
	arr = np.fromfile(
		path,
		dtype=dtype,
		count=shape[0] * M,
		offset=offset * M * dtype.itemsize # Offset is in bytes
	)
	arr.shape = shape
	return arr