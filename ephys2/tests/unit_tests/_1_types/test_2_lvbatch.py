'''
Test LVBatch
'''
import random
import pytest
import numpy as np

from ephys2.lib.types.lvbatch import *

def test_overlapping_append():
	lb1 = np.array([5, 2, 4, 2, 4, 6, 0, 1, 2])
	lb2 = np.array([7, 3, 5, 2, 9, 8, 2, 5, 3])
	O = 4 # overlap
	N1, N2 = lb1.size, lb2.size
	M = random.randint(5, 20)

	lv1 = LVBatch.random_generate(M, N1, overlap=0, labels=lb1)
	lv2 = LVBatch.random_generate(M, N2, overlap=O, labels=lb2)
	lv1.append(lv2)

	exp_lb = np.array([
		5, 2, 4, 2, 4, 6, 0, 1, 2,
		9, 8, 2, 5, 3
	])

	assert lv1.overlap == 0
	assert lv1.size == N1 + N2 - O
	assert np.allclose(lv1.labels, exp_lb)

def test_split():
	N, K = 20, 5
	M = random.randint(5, 20)
	lb = random_labeling(N, K)
	lv1 = LVBatch.random_generate(M, N, overlap=0, labels=lb.copy())
	iat = 11
	lv2 = lv1.split(iat)

	lb1, lb2 = lb[iat:], lb[:iat]

	assert lv1.size == lb1.size
	assert lv1.overlap == 0
	assert lv2.size == lb2.size
	assert lv2.overlap == 0
	assert np.allclose(lv1.labels, lb1)
	assert np.allclose(lv2.labels, lb2)
