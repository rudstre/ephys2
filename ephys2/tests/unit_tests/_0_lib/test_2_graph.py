'''
Tests of graph algorithms
'''
import numpy as np
import pytest

from ephys2.lib.graph import *

def test_pairs_to_ev_graph():
	pairs = [(0, 3), (1, 2), (1, 4)]
	assert np.allclose(
		pairs_to_ev_graph(pairs, 5).toarray(),
		np.array([
			[1, 0, 0],
			[0, 1, 1],
			[0, 1, 0],
			[1, 0, 0],
			[0, 0, 1]
		], dtype=bool).T
	)

	