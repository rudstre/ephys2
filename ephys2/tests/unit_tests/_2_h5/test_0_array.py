'''
Tests of H5 array serialization
'''

import numpy as np
import numpy.typing as npt
import random
import os
import pytest
import pdb

from tests.utils import rel_path
from .utils import *

from ephys2.lib.h5.array import *

'''
Test batch writing/loading
'''

def do_batch_test_array(inputs: List[npt.NDArray], ndim: int, dtype: np.dtype):
	do_batch_test(
		H5ArraySerializer,
		lambda A, B: np.allclose(A, B),
		inputs
	)

def test_1d():
	do_batch_test_array([
		np.random.randn(random.randint(1, 100)) for _ in range(10)
	], 1, float)

def test_Nd():
	M = random.randint(10, 100)
	do_batch_test_array([
		np.random.randn(random.randint(1, 100), M) for _ in range(10)
	], M, float)

def test_empty():
	M = random.randint(10, 100)
	do_batch_test_array([], M, float)


'''
Test end-to-end
'''

def do_reserialize_test_array(inputs: List[npt.NDArray], expected: npt.NDArray, npartitions: int):
	do_reserialize_test(
		H5ArraySerializer,
		H5ArraySerializer,
		lambda A, B: np.allclose(A, B),
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d():
	xs = [np.random.randn(random.randint(1, 10)) for _ in range(10)]
	y = np.concatenate(xs)
	do_reserialize_test_array(xs, y, 4)

def test_e2e_Nd():
	M = random.randint(10, 100)
	xs = [np.random.randn(random.randint(1, 10), M) for _ in range(10)]
	y = np.concatenate(xs, axis=0)
	do_reserialize_test_array(xs, y, 6)

def test_e2e_single():
	M = random.randint(10, 100)
	xs = [np.random.randn(random.randint(1, 10), M) for _ in range(10)]
	y = np.concatenate(xs, axis=0)
	do_reserialize_test_array(xs, y, 1)

def test_e2e_underworked():
	M = random.randint(10, 100)
	xs = [np.random.randn(random.randint(1, 10), M) for _ in range(10)]
	y = np.concatenate(xs, axis=0)
	do_reserialize_test_array(xs, y, 14)


'''
Test multiple loading
'''

def do_multi_test(inputs: List[npt.NDArray], expected: npt.NDArray, start: Optional[int], stop: Optional[int], overlap: int=0):
	paths = []
	files = []
	try:
		for i, data in enumerate(inputs):
			data_path = rel_path(f'test_multi_{i}.h5')
			paths.append(data_path)
			f = h5py.File(data_path, 'w')
			f.create_dataset('data', data=data)
			files.append(f)
		result = H5ArraySerializer.load_multi([f['data'] for f in files], start, stop, overlap)
		assert np.allclose(result, expected)
	finally:
		for file, path in zip(files, paths):
			file.close()
			remove_if_exists(path)

@pytest.mark.repeat(3)
def test_multi_1d():
	xs = [np.random.randn(random.randint(1, 10)) for _ in range(10)]
	N = sum(x.size for x in xs)
	start = random.randint(0, N)
	stop = random.randint(start, N)
	overlap = random.randint(0, max(0, stop - start - 1))
	y = np.concatenate(xs)[start:stop]
	do_multi_test(xs, y, start, stop, overlap)

@pytest.mark.repeat(3)
def test_multi_nd():
	M = random.randint(10, 100)
	xs = [np.random.randn(random.randint(1, 10), M) for _ in range(10)]
	N = sum(x.shape[0] for x in xs)
	start = random.randint(0, N)
	stop = random.randint(start, N)
	overlap = random.randint(0, max(0, stop - start - 1))
	y = np.concatenate(xs, axis=0)[start:stop]
	do_multi_test(xs, y, start, stop, overlap)


