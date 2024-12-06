'''
Accuracy tests of SPC C++ port against reference implementation.
'''

import pdb
import pytest
import numpy as np

from tests.utils import rel_path

from ephys2.lib.spc import *
from ephys2.lib.types import *

# Fails because of non-uniformity of random number generators chosen by C/C++. Also, this is a slow test.
def xtest_SPC_3Conc():
	data = np.loadtxt(rel_path('data/spc_3Conc/3Conc.dat'), dtype=np.float64)
	result1 = np.loadtxt(rel_path('data/spc_3Conc/3cout.dg_01.lab'), dtype=np.float64)
	temps1 = result1[:,1]
	clusters1 = result1[:,2:].astype(np.int64)

	temps2, clusters2 = run_spc(
		data,
		0.00,
		0.10,
		21,
		2000,
		11,
		random_seed=0
	)
	
	assert np.allclose(temps1, temps2), 'Temperatures inconsistent'
	assert np.allclose(clusters1, clusters2), 'Clusters inconsistent'

def test_dfs_paths():
	a, b, c, d, e, f, g = [SPCTree(None, []) for _ in range(7)]
	a.children = [b, c, g]
	c.children = [d]
	b.children = [e, f]

	got_paths = set()
	for path in a.dfs_paths():
		got_paths.add(frozenset(id(x) for x in path))

	exp_paths = set([
		frozenset([id(a), id(b), id(e)]),
		frozenset([id(a), id(b), id(f)]),
		frozenset([id(a), id(c), id(d)]),
		frozenset([id(a), id(g)])
	])
	assert got_paths == exp_paths
