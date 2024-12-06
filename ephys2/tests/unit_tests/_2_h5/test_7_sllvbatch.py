'''
Tests of H5 labeled events serialization
'''

from tests.utils import rel_path
from .utils import *

from ephys2.lib.h5.sllvbatch import *
from ephys2.lib.types.sllvbatch import *


'''
Test end-to-end
'''

def do_reserialize_test_sllvb(inputs: List[SLLVBatch], expected: SLLVBatch, npartitions: int):
	do_reserialize_test(
		H5SLLVBatchSerializer,
		H5SLLVBatchSerializer,
		lambda result, expected: result == expected.to_llvb(),
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d():
	M = 1
	N = 100
	B = 10
	R = random.randint(1, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVBatch.random_generate(M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVBatch.empty(M, B, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvb(xs, y, 4)

def test_e2e_Nd():
	M = random.randint(10, 100)
	N = 100
	B = 10
	R = random.randint(1, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVBatch.random_generate(M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVBatch.empty(M, B, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvb(xs, y, 6)

def test_e2e_overlap():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	R = random.randint(1, 10)
	k = 10
	NL = N * k - O * (k-1)
	C = 100
	xs = [SLLVBatch.random_generate(M, N, B, NL, R, C, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = SLLVBatch.empty(M, B, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvb(xs, y, 2)

def test_e2e_single():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	R = random.randint(1, 10)
	k = 10
	NL = N * k - O * (k-1)
	C = 100
	xs = [SLLVBatch.random_generate(M, N, B, NL, R, C, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = SLLVBatch.empty(M, B, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvb(xs, y, 1)

def test_e2e_underworked():
	M = random.randint(10, 100)
	N = 100
	B = 10
	O = 50
	R = random.randint(1, 10)
	k = 2
	NL = N * k - O * (k-1)
	C = 100
	xs = [SLLVBatch.random_generate(M, N, B, NL, R, C, overlap=(O if i > 0 else 0)) for i in range(k)]
	y = SLLVBatch.empty(M, B, R, C)
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvb(xs, y, 5)


''' Multi '''

def do_reserialize_test_sllvmb(inputs: List[SLLVMultiBatch], expected: SLLVMultiBatch, npartitions: int):
	do_reserialize_test(
		H5SLLVMultiBatchSerializer,
		H5SLLVMultiBatchSerializer,
		lambda result, expected: result == expected.to_llvmb(),
		inputs, 
		expected,
		npartitions
	)

def test_e2e_1d_m():
	M = 1
	N = 100
	B = 10
	R = random.randint(1, 10)
	K = random.randint(2, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVMultiBatch.random_generate(K, M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvmb(xs, y, 4)

def test_e2e_Nd_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	R = random.randint(1, 10)
	K = random.randint(2, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVMultiBatch.random_generate(K, M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvmb(xs, y, 6)

def test_e2e_overlap_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	R = random.randint(1, 10)
	K = random.randint(2, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVMultiBatch.random_generate(K, M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvmb(xs, y, 2)

def test_e2e_single_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	R = random.randint(1, 10)
	K = random.randint(2, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVMultiBatch.random_generate(K, M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvmb(xs, y, 1)

def test_e2e_underworked_m():
	M = random.randint(10, 100)
	N = 100
	B = 10
	R = random.randint(1, 10)
	K = random.randint(2, 10)
	k = 2
	NL = N * k
	C = 100
	xs = [SLLVMultiBatch.random_generate(K, M, N, B, NL, R, C) for _ in range(k)]
	y = SLLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvmb(xs, y, 5)

def test_e2e_full_links():
	M = random.randint(10, 100)
	N = 100
	B = 10
	R = random.randint(1, 10)
	K = random.randint(2, 10)
	k = 10
	NL = N * k
	C = 100
	xs = [SLLVMultiBatch.random_generate(K, M, N, B, NL, R, C) for _ in range(k)]
	xs[0].full_links = True
	y = SLLVMultiBatch.empty(xs[0])
	for x in xs:
		y.append(x)
	do_reserialize_test_sllvmb(xs, y, 6)
