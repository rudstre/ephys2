'''
Tests of base type methods.
'''
import numpy as np

from ephys2.lib.types.vbatch import *

'''
Test class methods
'''

def test_vb_append():
	N1, N2 = 10, 20
	M = 5
	vb1 = VBatch.random_generate(M, size=N1)
	vb2 = VBatch.random_generate(M, size=N2)
	vb1_, vb2_ = vb1.copy(), vb2.copy()
	vb1.append(vb2)
	assert vb1.ndim == M
	assert vb1.size == N1 + N2
	assert vb1.overlap == 0
	assert np.allclose(vb1.time, np.concatenate((vb1_.time, vb2_.time)))
	assert np.allclose(vb1.data, np.concatenate((vb1_.data, vb2_.data), axis=0))

def test_vb_append_overlap():
	N1, N2 = 10, 20
	M = 5
	O = 5
	vb1 = VBatch.random_generate(M, size=N1)
	vb2 = VBatch.random_generate(M, size=N2, overlap=O)
	vb1_, vb2_ = vb1.copy(), vb2.copy()
	vb1.append(vb2)
	assert vb1.ndim == M
	assert vb1.size == N1 + N2 - O
	assert vb1.overlap == 0
	assert np.allclose(vb1.time, np.concatenate((vb1_.time, vb2_.time[O:])))
	assert np.allclose(vb1.data, np.concatenate((vb1_.data, vb2_.data[O:]), axis=0))

def test_vb_split():
	N = 20
	M = 5
	iat = 6
	vb = VBatch.random_generate(M, size=N)
	vb_ = vb.copy()
	vb__ = vb.split(iat)
	assert vb__.size == iat
	assert vb__.overlap == 0
	assert vb__.ndim == M
	assert np.allclose(vb__.time, vb_.time[:iat])
	assert np.allclose(vb__.data, vb_.data[:iat])
	assert vb.size == N - iat
	assert vb.ndim == M
	assert vb.overlap == 0
	assert np.allclose(vb.time, vb_.time[iat:])
	assert np.allclose(vb.data, vb_.data[iat:])

def test_vb_split_overlap():
	N = 20
	M = 5
	iat = 6
	vb = VBatch.random_generate(M, size=N, overlap=3)
	vb_ = vb.copy()
	vb__ = vb.split(iat)
	assert vb__.size == iat
	assert vb__.overlap == 3
	assert vb__.ndim == M
	assert np.allclose(vb__.time, vb_.time[:iat])
	assert np.allclose(vb__.data, vb_.data[:iat])
	assert vb.size == N - iat
	assert vb.ndim == M
	assert vb.overlap == 0
	assert np.allclose(vb.time, vb_.time[iat:])
	assert np.allclose(vb.data, vb_.data[iat:])

def test_vb_append_split():
	M = 5
	O = 8 
	vb1 = VBatch.random_generate(M)
	N1 = vb1.size
	vb2 = VBatch.random_generate(M)
	vb1_, vb2_ = vb1.copy(), vb2.copy()
	vb1.append(vb2)
	vb2 = vb1
	vb1 = vb2.split(N1)
	assert vb1 == vb1_
	assert vb2 == vb2_

def test_vb_split_append():
	N = 20
	M = 8
	iat = 6
	vb2 = VBatch.random_generate(M, size=N)
	vb_ = vb2.copy()
	vb1 = vb2.split(iat)
	vb1.append(vb2)
	assert vb_ == vb1

def test_vb_remove_overlap():
	M, N = random.randint(1, 10), random.randint(10, 100)
	O = random.randint(1, N)
	vb = VBatch.random_generate(M, size=N, overlap=O)
	t, d = vb.time.copy(), vb.data.copy()
	vb.remove_overlap()
	assert vb.overlap == 0
	assert vb.size == N - O
	assert vb.ndim == M
	assert np.allclose(vb.time, t[O:])
	assert np.allclose(vb.data, d[O:])
