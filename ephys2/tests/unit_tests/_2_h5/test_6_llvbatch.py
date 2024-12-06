'''
Tests of H5 labeled events serialization
'''

from tests.utils import rel_path
from .utils import *

from ephys2.lib.h5.llvbatch import *
from ephys2.lib.types.llvbatch import *


'''
Test end-to-end
'''

def do_reserialize_test_llvb(inputs: List[LLVBatch], expected: LLVBatch, npartitions: int):
	do_reserialize_test(
		H5LLVBatchSerializer,
		H5LLVBatchSerializer,
		lambda result, expected: result == expected,
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d():
	M = 1
	N = 100
	B = 10
	k = 10
	NL = k * N
	xs = [LLVBatch.random_generate(M, N, B, NL) for _ in range(k)]
	y = LLVBatch.empty(M, B)
	for x in xs:
		y.append(x)
	do_reserialize_test_llvb(xs, y, 4)

def test_e2e_Nd():
	M = random.randint(10, 100)
	N = 100
	B = 10
	k = 10
	NL = k * N
	xs = [LLVBatch.random_generate(M, N, B, NL) for _ in range(k)]
	y = LLVBatch.empty(M, B)
	for x in xs:
		y.append(x)
	do_reserialize_test_llvb(xs, y, 6)

def test_e2e_overlap():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	k = 10
	NL = N * k - O * (k-1)
	xs = [LLVBatch.random_generate(M, N, B, NL, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = LLVBatch.empty(M, B)
	for x in xs:
		y.append(x)
	do_reserialize_test_llvb(xs, y, 2)

def test_e2e_single():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	k = 10
	NL = N * k - O * (k-1)
	xs = [LLVBatch.random_generate(M, N, B, NL, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = LLVBatch.empty(M, B)
	for x in xs:
		y.append(x)
	do_reserialize_test_llvb(xs, y, 1)

def test_e2e_underworked():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	k = 10
	NL = N * k - O * (k-1)
	xs = [LLVBatch.random_generate(M, N, B, NL, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = LLVBatch.empty(M, B)
	for x in xs:
		y.append(x)
	do_reserialize_test_llvb(xs, y, 5)


''' Multi '''

def do_reserialize_test_lvmb(inputs: List[LLVMultiBatch], expected: LLVMultiBatch, npartitions: int):
	do_reserialize_test(
		H5LLVMultiBatchSerializer,
		H5LLVMultiBatchSerializer,
		lambda result, expected: result == expected,
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d_m():
	M = 1
	N = 100
	B = 10
	K = random.randint(2, 10)
	k = 10
	NL = k * N
	xs = [LLVMultiBatch.random_generate(K, M, N, B, NL) for _ in range(k)]
	y = LLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_lvmb(xs, y, 4)

def test_e2e_Nd_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	K = random.randint(2, 10)
	k = 10
	NL = k * N
	xs = [LLVMultiBatch.random_generate(K, M, N, B, NL) for _ in range(k)]
	y = LLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_lvmb(xs, y, 6)

def test_e2e_overlap_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	K = random.randint(2, 10)
	k = 10
	NL = N * k - O * (k-1)
	xs = [LLVMultiBatch.random_generate(K, M, N, B, NL, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = LLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_lvmb(xs, y, 2)

def test_e2e_single_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	K = random.randint(2, 10)
	k = 10
	NL = N * k - O * (k-1)
	xs = [LLVMultiBatch.random_generate(K, M, N, B, NL, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = LLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_lvmb(xs, y, 1)

def test_e2e_underworked_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	K = random.randint(2, 10)
	k = 2
	NL = N * k - O * (k-1)
	xs = [LLVMultiBatch.random_generate(K, M, N, B, NL, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = LLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_lvmb(xs, y, 5)

def test_e2e_full_links():
	M = random.randint(10, 100)
	N = 100
	B = 10
	K = random.randint(2, 10)
	k = 10
	NL = k * N
	xs = [LLVMultiBatch.random_generate(K, M, N, B, NL) for _ in range(k)]
	xs[0].full_links = True
	y = LLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_lvmb(xs, y, 6)



