'''
Sparse matrix class & functions
'''

from os import stat
from typing import Tuple, Iterable, List
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import scipy.sparse as sp

''' Data structure: Compressed-Sparse Row matrix ''' 

@dataclass
class CSRMatrix:
	'''
	The primary difference with scipy's csr_matrix is that indices and indptr are forced
	to be int64. Additionally, no math operations are supported, this is merely a data container.
	'''
	data: np.ndarray
	indices: npt.NDArray[np.int64]
	indptr: npt.NDArray[np.int64]
	shape: Tuple[int, int]

	def __post_init__(self):
		self.dtype = self.data.dtype
		self.shape = (int(self.shape[0]), self.shape[1])
		self.indices = self.indices.astype(np.int64, copy=False)
		self.indptr = self.indptr.astype(np.int64, copy=False)
		assert self.shape[0] == self.indptr.size - 1, 'Invalid shape'
		assert self.indptr[0] == 0, 'Invalid indptr'

	def to_sp(self) -> sp.csr_matrix:
		''' Converts to int32; to be used only for testing purposes '''
		return sp.csr_matrix((self.data, self.indices, self.indptr), shape=self.shape, dtype=self.dtype)

	def check_format(self):
		self.to_sp().check_format(full_check=True)

	def toarray(self) -> np.ndarray:
		return self.to_sp().toarray()

	def get_row_indices(self, row: int) -> npt.NDArray[np.int64]:
		return self.indices[self.indptr[row]:self.indptr[row + 1]]

	def copy(self) -> 'CSRMatrix':
		return CSRMatrix(self.data.copy(), self.indices.copy(), self.indptr.copy(), self.shape)

	def tuple(self) -> Tuple[np.ndarray, npt.NDArray[np.int64], npt.NDArray[np.int64], Tuple[int, int]]:
		return (self.data, self.indices, self.indptr, self.shape)

	@staticmethod
	def from_sp(A: sp.csr_matrix):
		return CSRMatrix(A.data, A.indices, A.indptr, A.shape)

	def __eq__(self, other: 'CSRMatrix') -> bool:
		return (
			self.dtype == other.dtype and 
			self.shape == other.shape and 
			np.allclose(self.data, other.data) and 
			np.allclose(self.indices, other.indices) and
			np.allclose(self.indptr, other.indptr)
		)

''' Algorithms '''

def csr_split(A: CSRMatrix, iat: int) -> Tuple[CSRMatrix, CSRMatrix]:
	'''
	Split a CSR matrix at a row index.
	'''
	N, M = A.shape
	assert iat <= N
	if iat == 0:
		return empty_csr(M, dtype=A.dtype), A
	elif iat == N:
		return A, empty_csr(M, dtype=A.dtype)
	indptr1 = A.indptr[:iat+1].copy()
	indptr2 = A.indptr[iat+1:].copy()
	offset = indptr1[-1]
	indices1 = A.indices[:offset].copy()
	data1 = A.data[:offset].copy()
	indices2 = A.indices[offset:].copy()
	data2 = A.data[offset:].copy()
	indptr2 -= offset
	indptr2 = np.insert(indptr2, 0, 0)
	A1 = CSRMatrix(data1, indices1, indptr1, (iat, M))
	A2 = CSRMatrix(data2, indices2, indptr2, (N-iat, M))
	return A1, A2

def csr_concat(Xs: Iterable[CSRMatrix], mode='AP') -> CSRMatrix:
	'''
	Concatenate two CSR matrices along the first dimension, in one of two modes:
	1. 'AP' append mode, taking the maxima of the 2nd dimension.
	2. 'DS' direct-sum mode, taking the sums of the 2nd dimension.
	'''
	data, indices, indptr = [], [], []
	last_indptr = 0
	N, M = 0, 0
	for i, X in enumerate(Xs):
		if i == 0:
			indptr.append(X.indptr)
		else:
			indptr.append(X.indptr[1:] + last_indptr) # Suppress leading zero, increment by offset
		if mode == 'AP':
			indices.append(X.indices)
			M = max(M, X.shape[1])
		elif mode == 'DS':
			indices.append(X.indices + M)
			M += X.shape[1]
		else:
			raise ValueError(f"Expected mode == 'DS' or 'AP', got {mode} instead" )
		data.append(X.data)
		last_indptr += X.indptr[-1]
		N += X.shape[0]
	data, indices, indptr = np.concatenate(data), np.concatenate(indices), np.concatenate(indptr)
	return CSRMatrix(data, indices, indptr, (N, M))

def csr_col_offset(A: CSRMatrix, M_offset: int) -> CSRMatrix:
	'''
	Offset the column entries of a CSR matrix by an integer. Typically used to construct block matrices using direct-sums.
	Returns a copy.
	'''
	return CSRMatrix(
		A.data, A.indices + M_offset, A.indptr,
		(A.shape[0], A.shape[1] + M_offset)
	)

def csr_allclose(M1: CSRMatrix, M2: CSRMatrix, match_axis2=True) -> bool:
	'''
	Like np.allclose() but for CSR matrices.
	Assumes both matrices have suppressed zeros
	match_axis2: whether both shapes should match along the 2nd axis.
	'''
	return (
		(
			(match_axis2 and M1.shape == M2.shape) or 
			(not match_axis2 and M1.shape[0] == M2.shape[0])
		) and
		np.allclose(M1.data, M2.data) and 
		np.allclose(M1.indices, M2.indices) and 
		np.allclose(M1.indptr, M2.indptr)
	)

def csr_getcol(A: CSRMatrix, j: int) -> Tuple[np.ndarray, np.ndarray]:
	'''
	Get the jth column of a CSR matrix.
	Slow operation; intended for testing purposes (use C++ version instead).
	'''
	row_indices, col_data = [], []
	for i in range(A.indptr.size - 1):
		indices = A.indices[A.indptr[i]:A.indptr[i+1]]
		mask = indices == j
		indices = indices[mask]
		if indices.size > 0:
			row_indices.append(i)
			col_data.append(A.data[A.indptr[i]:A.indptr[i+1]][mask][0])
	return np.array(row_indices), np.array(col_data)

def empty_csr(ndim: int, dtype: np.dtype=float) -> CSRMatrix:
	'''
	Construct an empty CSR matrix of a given row dimension.
	'''
	return CSRMatrix(np.array([], dtype=dtype), np.array([]), np.array([0]), (0,ndim))

