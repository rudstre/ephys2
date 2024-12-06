'''
Tests of base type methods.
'''
import numpy as np

from ephys2.lib.types.ltbatch import *

'''
Test class methods
'''

def test_vb_append():
	N1, N2 = 10, 20
	vb1 = LTBatch.random_generate(size=N1)
	vb2 = LTBatch.random_generate(size=N2)
	vb1_, vb2_ = vb1.copy(), vb2.copy()
	vb1.append(vb2)
	assert vb1.size == N1 + N2
	assert vb1.overlap == 0
	assert np.allclose(vb1.time, np.concatenate((vb1_.time, vb2_.time)))
	assert np.allclose(vb1.labels, np.concatenate((vb1_.labels, vb2_.labels)))

def test_vb_append_overlap():
	N1, N2 = 10, 20
	O = 5
	vb1 = LTBatch.random_generate(size=N1)
	vb2 = LTBatch.random_generate(size=N2, overlap=O)
	vb1_, vb2_ = vb1.copy(), vb2.copy()
	vb1.append(vb2)
	assert vb1.size == N1 + N2 - O
	assert vb1.overlap == 0
	assert np.allclose(vb1.time, np.concatenate((vb1_.time, vb2_.time[O:])))
	assert np.allclose(vb1.labels, np.concatenate((vb1_.labels, vb2_.labels[O:])))

def test_vb_split():
	N = 20
	iat = 6
	vb = LTBatch.random_generate(size=N)
	vb_ = vb.copy()
	vb__ = vb.split(iat)
	assert vb__.size == iat
	assert vb__.overlap == 0
	assert np.allclose(vb__.time, vb_.time[:iat])
	assert np.allclose(vb__.labels, vb_.labels[:iat])
	assert vb.size == N - iat
	assert vb.overlap == 0
	assert np.allclose(vb.time, vb_.time[iat:])
	assert np.allclose(vb.labels, vb_.labels[iat:])

def test_vb_split_overlap():
	N = 20
	iat = 6
	vb = LTBatch.random_generate(size=N, overlap=3)
	vb_ = vb.copy()
	vb__ = vb.split(iat)
	assert vb__.size == iat
	assert vb__.overlap == 3
	assert np.allclose(vb__.time, vb_.time[:iat])
	assert np.allclose(vb__.labels, vb_.labels[:iat])
	assert vb.size == N - iat
	assert vb.overlap == 0
	assert np.allclose(vb.time, vb_.time[iat:])
	assert np.allclose(vb.labels, vb_.labels[iat:])

def test_vb_append_split():
	O = 8 
	vb1 = LTBatch.random_generate()
	N1 = vb1.size
	vb2 = LTBatch.random_generate()
	vb1_, vb2_ = vb1.copy(), vb2.copy()
	vb1.append(vb2)
	vb2 = vb1
	vb1 = vb2.split(N1)
	assert vb1 == vb1_
	assert vb2 == vb2_

def test_vb_split_append():
	N = 20
	iat = 6
	vb2 = LTBatch.random_generate(size=N)
	vb_ = vb2.copy()
	vb1 = vb2.split(iat)
	vb1.append(vb2)
	assert vb_ == vb1
