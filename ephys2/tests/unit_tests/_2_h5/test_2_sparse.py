'''
Tests of H5 sparse matrix serialization
'''

import numpy as np
import numpy.typing as npt
import random
import os
import scipy.sparse as sp
import pytest

from tests.utils import *
from .utils import *

from ephys2.lib.h5.sparse import *
from ephys2.lib.sparse import *


'''
Test end-to-end
(only tests append-only mode reserializer)
'''

def do_reserialize_test_CSR(inputs: List[CSRMatrix], expected: CSRMatrix, npartitions: int, **kwargs):
	do_reserialize_test(
		H5CSRSerializer,
		H5CSRSerializer,
		lambda result, expected: result == expected,
		inputs, 
		expected,
		npartitions,
		**kwargs
	)

def test_e2e_1d():
	M = 1
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr', density=0.1)) for _ in range(10)]
	y = csr_concat(xs)
	do_reserialize_test_CSR(xs, y, 4)

def test_e2e_Nd():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr')) for _ in range(10)]
	y = csr_concat(xs)
	do_reserialize_test_CSR(xs, y, 6)

def test_e2e_single():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr')) for _ in range(10)]
	y = csr_concat(xs)
	do_reserialize_test_CSR(xs, y, 1)

def test_e2e_underworked():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr')) for _ in range(10)]
	y = csr_concat(xs)
	do_reserialize_test_CSR(xs, y, 12)

def test_e2e_empty_ndim():
	M = random.randint(10, 100)
	do_reserialize_test_CSR([empty_csr(M)], empty_csr(M), 6)

'''
Test partial loading
(only tests append-only mode reserializer)
'''

def test_e2e_1d_partial():
	M = 1
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr', density=0.1)) for _ in range(10)]
	y = csr_concat(xs)
	iat = y.shape[0] // 2
	_, y = csr_split(y, iat)
	do_reserialize_test_CSR(xs, y, 4, start=iat)

def test_e2e_Nd_partial():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr')) for _ in range(10)]
	y = csr_concat(xs)
	iat = y.shape[0] // 2
	_, y = csr_split(y, iat)
	do_reserialize_test_CSR(xs, y, 6, start=iat)

def test_e2e_single_partial():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr')) for _ in range(10)]
	y = csr_concat(xs)
	iat = y.shape[0] // 2
	_, y = csr_split(y, iat)
	do_reserialize_test_CSR(xs, y, 1, start=iat)

def test_e2e_underworked_partial():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 100), M, format='csr')) for _ in range(10)]
	y = csr_concat(xs)
	iat = y.shape[0] // 2
	_, y = csr_split(y, iat)
	do_reserialize_test_CSR(xs, y, 12, start=iat)

'''
Test sparse indexing
'''

def do_sparse_test_CSR(arg: CSRMatrix, indices: npt.NDArray[np.int64]):
	filepath = rel_path('data/test.h5')
	try:
		with h5py.File(filepath, 'w') as file:
			file.create_dataset('data', data=arg.data)
			file.create_dataset('indices', data=arg.indices)
			file.create_dataset('indptr', data=arg.indptr)
			file.attrs['shape'] = arg.shape
			H5CSRSerializer.check(file, full=True)
			result = H5CSRSerializer.load_sparse(file, indices)
			result.check_format()
			expected = CSRMatrix.from_sp(sp.csr_matrix(arg.toarray()[indices]))
			assert result == expected
	finally:
		remove_if_exists(filepath)

def do_sparse_test_CSR_randomized(dtype: np.dtype):
	M, N = random.randint(1, 20), random.randint(1, 20)
	d = np.random.uniform(0.1, 0.5)
	A = sp.random(M, N, density=d, dtype=dtype).tocsr()
	indices = np.arange(M)
	mask = (np.random.randn(M) > 0.5)
	indices = indices[mask]
	do_sparse_test_CSR(CSRMatrix.from_sp(A), indices)

def test_sparse_load_csr_bool():
	do_sparse_test_CSR_randomized(bool)

def test_sparse_load_csr_float():
	do_sparse_test_CSR_randomized(np.float32)


'''
Test multiple loading
'''

def do_multi_test(inputs: List[CSRMatrix], expected: CSRMatrix, start: Optional[int], stop: Optional[int], overlap: int=0):
	paths = []
	try:
		files = []
		for i, data in enumerate(inputs):
			data_path = rel_path(f'test_multi_{i}.h5')
			paths.append(data_path)
			f = h5py.File(data_path, 'w')
			f.create_dataset('data', data=data.data)
			f.create_dataset('indices', data=data.indices)
			f.create_dataset('indptr', data=data.indptr)
			f.attrs['shape'] = data.shape
			files.append(f)
		result = H5CSRSerializer.load_multi(files, start, stop, overlap)
		assert result == expected
	finally:
		for path in paths:
			remove_if_exists(path)

@pytest.mark.repeat(3)
def test_multi_1d():
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 10), 1, density=0.5).tocsr()) for _ in range(10)]
	N = sum(x.shape[0] for x in xs)
	start = random.randint(0, N)
	stop = random.randint(start, N)
	overlap = random.randint(0, stop - start)
	y = csr_concat(xs)
	y, _ = csr_split(y, stop)
	_, y = csr_split(y, start)
	do_multi_test(xs, y, start, stop, overlap)

@pytest.mark.repeat(3)
def test_multi_nd():
	M = random.randint(10, 100)
	xs = [CSRMatrix.from_sp(sp.rand(random.randint(1, 10), M, density=0.5).tocsr()) for _ in range(10)]
	N = sum(x.shape[0] for x in xs)
	start = random.randint(0, N)
	stop = random.randint(start, N)
	overlap = random.randint(0, stop - start)
	y = csr_concat(xs)
	y, _ = csr_split(y, stop)
	_, y = csr_split(y, start)
	do_multi_test(xs, y, start, stop, overlap)

