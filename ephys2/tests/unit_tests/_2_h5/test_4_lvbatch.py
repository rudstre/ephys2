'''
Tests of H5 labeled events serialization
'''
import pytest
import random

from tests.utils import rel_path
from .utils import *

from ephys2.lib.h5.lvbatch import *
from ephys2.lib.types.lvbatch import *

@pytest.mark.repeat(3)
def test_e2e():
	D = 10
	Ns = [random.randint(1, 20) for _ in range(D)]
	Ks = [random.randint(1, N) for N in Ns]
	Os = [0] + [random.randint(0, min(Ns[i-1], Ns[i])) for i in range(1, D)]
	M = random.randint(5, 20)
	lvs = [
		LVBatch.random_generate(
			M, size=N, labels=random_labeling(N, K), overlap=O
		) for N, K, O in zip(Ns, Ks, Os)
	]

	exp_lv = lvs[0].copy()
	for lv in lvs[1:]:
		exp_lv.append(lv)

	do_reserialize_test(
		H5LVBatchSerializer,
		H5LVBatchSerializer,
		lambda result, expected: result == expected,
		lvs,
		exp_lv,
		6
	)