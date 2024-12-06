'''
Test sparse matrix methods
'''

import random
import numpy as np
import scipy.sparse as sp

from ephys2.lib.sparse import *

def test_csr_split():
	N1, N2 = random.randint(10, 100), random.randint(10, 100)
	M = 50
	A1 = sp.rand(N1, M, format='csr')
	A2 = sp.rand(N2, M, format='csr')
	A = sp.vstack([A1, A2], format='csr')
	B1, B2 = csr_split(CSRMatrix.from_sp(A), N1)
	B1.check_format()
	B2.check_format()
	assert np.allclose(A1.toarray(), B1.toarray())
	assert np.allclose(A2.toarray(), B2.toarray())

def test_csr_concat():
	N1, N2 = random.randint(10, 100), random.randint(10, 100)
	M = 50
	A1 = sp.rand(N1, M, format='csr')
	A2 = sp.rand(N2, M, format='csr')
	A = sp.vstack([A1, A2], format='csr')
	A_ = csr_concat((CSRMatrix.from_sp(A1), CSRMatrix.from_sp(A2)))
	A_.check_format()
	assert np.allclose(A.toarray(), A_.toarray())

def test_csr_allclose_t():
	# Test random true conditions
	M, N = random.randint(1, 10), random.randint(1, 10)
	for i in range(10):
		A = CSRMatrix.from_sp(sp.rand(M, N, format='csr', density=0.1*i))
		B = CSRMatrix(A.data, A.indices, A.indptr, A.shape)
		assert csr_allclose(A, B)

def test_csr_allclose_f():
	# Test random (probably) false conditions
	M, N = random.randint(1, 10), random.randint(1, 10)
	for i in range(10):
		A, B = sp.rand(M, N, format='csr', density=0.1*i), sp.rand(M, N, format='csr', density=0.1*i)
		assert np.allclose(A.toarray(), B.toarray()) == csr_allclose(CSRMatrix.from_sp(A), CSRMatrix.from_sp(B))

def test_csr_allclose_td():
	# Test differing 2nd axis
	M1, N = random.randint(1, 10), random.randint(1, 10)
	for i in range(10):
		A = sp.rand(N, M1, format='csr', density=0.1*i)
		M2 = random.randint(M1, 100)
		B = sp.csr_matrix((A.data, A.indices, A.indptr), shape=(N, M2))
		assert csr_allclose(CSRMatrix.from_sp(A), CSRMatrix.from_sp(B), match_axis2=False)

