'''
Tests of sequence alignment algorithm
'''
import numpy as np
import pytest
import random

from ephys2.lib.types import random_labeling
from ephys2.lib.seq_align import seq_align
from ephys2 import _cpp

def random_times(N, min_dt: int=1, max_dt: int=1000):
	return np.cumsum(np.random.randint(min_dt, max_dt, size=N)).astype(np.int64)

def test_seq_align_empty():
	max_dist = random.randint(1, 10)
	fill_val = -1

	xs = np.array([], dtype=np.int64)

	res = _cpp.align_sequences(xs, xs, xs, xs, max_dist, fill_val)
	exp = np.array([])
	exp.shape = (0,2)

	assert np.allclose(res, exp)


@pytest.mark.repeat(5)
def test_seq_align():
	N1 = random.randint(10, 100)
	N2 = random.randint(10, 100)
	K1 = random.randint(1, N1)
	K2 = random.randint(1, N2)

	t1 = random_times(N1)
	t2 = random_times(N2)
	v1 = random_labeling(N1, K1)
	v2 = random_labeling(N2, K2)

	max_dist = random.randint(1, 10)
	fill_val = -1

	res1 = seq_align(t1, v1, t2, v2, max_dist)
	res2 = _cpp.align_sequences(t1, t2, v1, v2, max_dist, fill_val)

	assert np.allclose(res1, res2)
