import pytest
import numpy as np
import random

from ephys2.lib.types import *
from ephys2.lib.sparse import *
from ephys2.lib.cluster import *

def test_overlapping_append():
	N1, N2 = 20, 20
	M = random.randint(5, 20)
	O = 10 # overlap
	B = 10
	NL = N1 + N2
	lv1 = LLVBatch.random_generate(M, N1, B, NL, overlap=0)
	lv2 = LLVBatch.random_generate(M, N2, B, NL, overlap=O)
	exp_lb = np.concatenate((lv1.labels, lv2.labels[O:]))
	exp_li = csr_concat((lv1.linkage, lv2.linkage))
	lv1.append(lv2)
	assert np.allclose(lv1.labels, exp_lb)
	assert lv1.linkage == exp_li

def test_split():
	N = 20
	M = random.randint(5, 20)
	B = 10
	lv1 = LLVBatch.random_generate(M, N, B, N, overlap=0)
	lv1_ = lv1.copy()
	iat = 11
	lv2 = lv1.split(iat)
	assert lv1_[iat:] == lv1
	assert lv1_[:iat] == lv2