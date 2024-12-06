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

from ephys2.lib.h5.vbatch import *
from ephys2.lib.types import *


'''
Test end-to-end
'''

def do_reserialize_test_vb(inputs: List[VBatch], expected: VBatch, npartitions: int, **kwargs):
	do_reserialize_test(
		H5VBatchSerializer,
		H5VBatchSerializer,
		lambda result, expected: result == expected and result.overlap == expected.overlap,
		inputs, 
		expected,
		npartitions,
		**kwargs
	)

def test_e2e_1d():
	M = 1
	xs = [VBatch.random_generate(M) for _ in range(10)]
	y = VBatch.empty(M)
	for x in xs:
		y.append(x)
	do_reserialize_test_vb(xs, y, 4)

def test_e2e_Nd():
	M = random.randint(10, 100)
	xs = [VBatch.random_generate(M) for _ in range(10)]
	y = VBatch.empty(M)
	for x in xs:
		y.append(x)
	do_reserialize_test_vb(xs, y, 6)

def test_e2e_Nd():
	M = random.randint(10, 100)
	xs = [VBatch.random_generate(M) for _ in range(10)]
	y = xs[0].copy()
	for x in xs[1:]:
		y.append(x)
	do_reserialize_test_vb(xs, y, 6)

def test_e2e_overlap():
	M = random.randint(10, 100)
	O = 5
	xs = [VBatch.random_generate(M, overlap=(0 if i == 0 else O)) for i in range(10)]
	y = xs[0].copy()
	for x in xs[1:]:
		y.append(x)
	do_reserialize_test_vb(xs, y, 6)

def test_e2e_load_overlap_1():
	M = random.randint(10, 100)
	N = 100
	O = 20
	start = 10
	xs = [VBatch.random_generate(M, size=N)]
	y = xs[0].copy()
	y.split(start)
	y.overlap = O
	do_reserialize_test_vb(xs, y, 1, start=start, overlap=O)

def test_e2e_load_overlap_2():
	M = random.randint(10, 100)
	N = 100
	O = 120
	start = 10
	xs = [VBatch.random_generate(M, size=N)]
	y = VBatch.empty(M)
	do_reserialize_test_vb(xs, y, 1, start=start, overlap=O)

def test_e2e_overworked():
	M = random.randint(10, 100)
	xs = [VBatch.random_generate(M) for _ in range(10)]
	y = VBatch.empty(M)
	for x in xs:
		y.append(x)
	do_reserialize_test_vb(xs, y, 1)

def test_e2e_underworked():
	M = random.randint(10, 100)
	xs = [VBatch.random_generate(M) for _ in range(10)]
	y = VBatch.empty(M)
	for x in xs:
		y.append(x)
	do_reserialize_test_vb(xs, y, 12)

''' Multi '''

def do_reserialize_test_vmb(inputs: List[VMultiBatch], expected: VMultiBatch, npartitions: int):
	do_reserialize_test(
		H5VMultiBatchSerializer,
		H5VMultiBatchSerializer,
		lambda result, expected: result == expected,
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d_m():
	M = 1
	K = random.randint(2, 10)
	xs = [VMultiBatch.random_generate(K, M) for _ in range(10)]
	y = VMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_vmb(xs, y, 4)

def test_e2e_Nd_m():
	M = random.randint(10, 100)
	K = random.randint(2, 10)
	xs = [VMultiBatch.random_generate(K, M) for _ in range(10)]
	y = VMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_vmb(xs, y, 6)

def test_e2e_Nd_m():
	M = random.randint(10, 100)
	K = random.randint(2, 10)
	xs = [VMultiBatch.random_generate(K, M) for _ in range(10)]
	y = xs[0].copy()
	for x in xs[1:]:
		y.append(x)
	do_reserialize_test_vmb(xs, y, 6)

def test_e2e_overlap_m():
	M = random.randint(10, 100)
	O = 5
	K = random.randint(2, 10)
	xs = [VMultiBatch.random_generate(K, M, overlap=(0 if i == 0 else O)) for i in range(10)]
	y = xs[0].copy()
	for x in xs[1:]:
		y.append(x)
	do_reserialize_test_vmb(xs, y, 6)

def test_e2e_overworked_m():
	M = random.randint(10, 100)
	K = random.randint(2, 10)
	xs = [VMultiBatch.random_generate(K, M) for _ in range(10)]
	y = VMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_vmb(xs, y, 1)

def test_e2e_underworked_m():
	M = random.randint(10, 100)
	K = random.randint(2, 10)
	xs = [VMultiBatch.random_generate(K, M) for _ in range(10)]
	y = VMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_vmb(xs, y, 12)


