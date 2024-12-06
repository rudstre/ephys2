'''
Tests of H5 array serialization
'''

import numpy as np
import numpy.typing as npt
import random
import os
import pdb

from tests.utils import rel_path
from .utils import *

from ephys2.lib.h5.tbatch import *
from ephys2.lib.types import *

'''
Test end-to-end
'''

def do_reserialize_test_tb(inputs: List[TBatch], expected: TBatch, npartitions: int, **kwargs):
	do_reserialize_test(
		H5TBatchSerializer,
		H5TBatchSerializer,
		lambda result, expected: result == expected and result.overlap == expected.overlap,
		inputs, 
		expected,
		npartitions,
		**kwargs
	)

def test_e2e_1d():
	xs = [TBatch.random_generate() for _ in range(10)]
	y = TBatch.empty()
	for x in xs:
		y.append(x)
	do_reserialize_test_tb(xs, y, 4)

def test_e2e_overlap():
	O = 5
	xs = [TBatch.random_generate(overlap=(0 if i == 0 else O)) for i in range(10)]
	y = xs[0].copy()
	for x in xs[1:]:
		y.append(x)
	do_reserialize_test_tb(xs, y, 6)

def test_e2e_load_overlap_1():
	N = 100
	O = 20
	start = 10
	xs = [TBatch.random_generate(size=N)]
	y = xs[0].copy()
	y.split(start)
	y.overlap = O
	do_reserialize_test_tb(xs, y, 1, start=start, overlap=O)

def test_e2e_load_overlap_2():
	N = 100
	O = 120
	start = 10
	xs = [TBatch.random_generate(size=N)]
	y = TBatch.empty()
	do_reserialize_test_tb(xs, y, 1, start=start, overlap=O)

def test_e2e_overworked():
	xs = [TBatch.random_generate() for _ in range(10)]
	y = TBatch.empty()
	for x in xs:
		y.append(x)
	do_reserialize_test_tb(xs, y, 1)

def test_e2e_underworked():
	xs = [TBatch.random_generate() for _ in range(10)]
	y = TBatch.empty()
	for x in xs:
		y.append(x)
	do_reserialize_test_tb(xs, y, 12)


''' Multi '''

def do_reserialize_test_ltmb(inputs: List[TMultiBatch], expected: TMultiBatch, npartitions: int):
	do_reserialize_test(
		H5TMultiBatchSerializer,
		H5TMultiBatchSerializer,
		lambda result, expected: result == expected,
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d_m():
	K = random.randint(2, 10)
	xs = [TMultiBatch.random_generate(K) for _ in range(10)]
	y = TMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_ltmb(xs, y, 4)

def test_e2e_overlap_m():
	O = 5
	K = random.randint(2, 10)
	xs = [TMultiBatch.random_generate(K, overlap=(0 if i == 0 else O)) for i in range(10)]
	y = xs[0].copy()
	for x in xs[1:]:
		y.append(x)
	do_reserialize_test_ltmb(xs, y, 6)

def test_e2e_overworked_m():
	K = random.randint(2, 10)
	xs = [TMultiBatch.random_generate(K) for _ in range(10)]
	y = TMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_ltmb(xs, y, 1)

def test_e2e_underworked_m():
	K = random.randint(2, 10)
	xs = [TMultiBatch.random_generate(K) for _ in range(10)]
	y = TMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_ltmb(xs, y, 12)


