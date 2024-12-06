'''
Tests of H5 summarized labeled events serialization
'''

from tests.utils import rel_path
from .utils import *

from ephys2.lib.h5.slvbatch import *
from ephys2.lib.types.slvbatch import *


'''
Test end-to-end
'''

def do_reserialize_test_slvb(inputs: List[SLVBatch], expected: SLVBatch, npartitions: int):
	do_reserialize_test(
		H5SLVBatchSerializer,
		H5SLVBatchSerializer,
		lambda result, expected: result == expected,
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d():
	M = 1
	N = 100
	R = random.randint(1, 10)
	C = 100
	xs = [SLVBatch.random_generate(M, N, R, C) for _ in range(10)]
	y = SLVBatch.empty(M, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_slvb(xs, y, 4)

def test_e2e_Nd():
	M = random.randint(10, 100)
	N = 100
	R = random.randint(1, 10)
	C = 100
	xs = [SLVBatch.random_generate(M, N, R, C) for _ in range(10)]
	y = SLVBatch.empty(M, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_slvb(xs, y, 6)

def test_e2e_overlap():
	M = random.randint(10, 100)
	N1, N2 = random.randint(2, 10), random.randint(2, 10)
	O = random.randint(1, N2)
	R = random.randint(1, 10)
	C = 100
	x1 = SLVBatch.random_generate(M, N1, R, C, overlap=0)
	x2 = SLVBatch.random_generate(M, N2, R, C, overlap=O)
	x1_, x2_ = x1.copy(), x2.copy()
	x1_.append(x2_)
	do_reserialize_test_slvb([x1, x2], x1_, 2)

def test_e2e_single():
	M = random.randint(10, 100)
	N1, N2 = random.randint(2, 10), random.randint(2, 10)
	O = random.randint(1, N2)
	C = 100
	R = random.randint(1, 10)
	x1 = SLVBatch.random_generate(M, N1, R, C, overlap=0)
	x2 = SLVBatch.random_generate(M, N2, R, C, overlap=O)
	x1_, x2_ = x1.copy(), x2.copy()
	x1_.append(x2_)
	do_reserialize_test_slvb([x1, x2], x1_, 1)

def test_e2e_underworked():
	M = random.randint(10, 100)
	N1, N2 = random.randint(2, 10), random.randint(2, 10)
	O = random.randint(1, N2)
	R = random.randint(1, 10)
	C = 100
	x1 = SLVBatch.random_generate(M, N1, R, C, overlap=0)
	x2 = SLVBatch.random_generate(M, N2, R, C, overlap=O)
	x1_, x2_ = x1.copy(), x2.copy()
	x1_.append(x2_)
	do_reserialize_test_slvb([x1, x2], x1_, 5)

