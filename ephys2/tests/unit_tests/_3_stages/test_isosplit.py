'''
Sanity tests of iso-split clustering algorithm
'''
import numpy as np

from ephys2.lib.isosplit import *

def xtest_n_points():
	X = np.arange(100)[:,np.newaxis].astype(np.float32)
	labels = isosplit5(
		X, random_seed=0, min_cluster_size=1
	)
	labels.sort()
	assert np.allclose(labels, np.array([1,2,3,4,5]))

def xtest_identical():
	X = np.array([[1], [1], [2], [2], [3]], dtype=np.float32)
	labels = isosplit5(
		X, random_seed=0, min_cluster_size=1
	)
	labels.sort()
	assert np.allclose(labels, np.array([1,1,2,2,3]))