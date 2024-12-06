'''
Test of cluster functions
'''
import numpy as np
import pytest

from ephys2.lib.cluster import *

def test_clustering_to_labeling():
	N = 10
	C = [
		np.array([4, 6, 1], dtype=np.int64),
		np.array([5], dtype=np.int64),
		np.array([9, 8], dtype=np.int64)
	]
	lb, K = clustering_to_labeling(C, N)
	assert np.allclose(lb, np.array([3, 0, 4, 5, 0, 1, 0, 6, 2, 2]))

def test_labeling_to_clustering():
	lb = np.array([0, 1, 5, 1, 4, 3, 0, 3, 3])
	C = labeling_to_clustering(lb)
	assert eq_clustering(
		C,
		[
			np.array([0, 6]),
			np.array([1, 3]),
			np.array([5, 7, 8]),
			np.array([4]),
			np.array([2]),
		]
	)

def test_labeling_to_clustering_indices():
	lb = np.array([0, 1, 5, 1, 4, 3, 0, 3, 3])
	ids = np.array([9, 8, 7, 6, 5, 4, 3, 2, 1])
	C = labeling_to_clustering(lb, indices=ids)
	assert eq_clustering(
		C,
		[
			np.array([9, 3]),
			np.array([8, 6]),
			np.array([4, 2, 1]),
			np.array([5]),
			np.array([7]),
		]
	)

def test_labeling_to_clustering_to_labeling():
	N, K = 20, 8
	lb = random_labeling(N, K)
	lb_, K_ = clustering_to_labeling(labeling_to_clustering(lb), N)
	assert K == K_
	assert np.allclose(lb, lb_)

def test_link_labels_degenerate():
	linkage = pairs_to_ev_graph([], 10)
	lb = np.arange(10)
	assert np.allclose(lb, link_labels_py(lb, linkage))
	assert np.allclose(lb, link_labels(lb, linkage))

def test_link_labels_chain():
	linkage = pairs_to_ev_graph([
		(0, 4), (1, 5), (2, 6), (3, 7),
	], 8)
	lb = np.array([0, 1, 2, 3, 4, 5, 6, 7])
	exp_lb = np.array([0, 1, 2, 3, 0, 1, 2, 3])
	assert np.allclose(exp_lb, link_labels_py(lb, linkage))
	assert np.allclose(exp_lb, link_labels(lb, linkage))

def test_link_labels_redundant():
	linkage = pairs_to_ev_graph([
		(0, 4), (1, 5), (2, 3), (0, 4)
	], 6)
	lb = np.array([0, 1, 2, 3, 4, 5])
	exp_lb = np.array([0, 1, 2, 2, 0, 1])
	assert np.allclose(exp_lb, link_labels_py(lb, linkage))
	assert np.allclose(exp_lb, link_labels(lb, linkage))

def test_link_labels_loopy():
	linkage = pairs_to_ev_graph([
		(0, 4), (4, 1), (1, 3), (3, 0), (2, 5)
	], 6)
	lb = np.array([0, 1, 2, 3, 4, 5])
	exp_lb = np.array([0, 0, 2, 0, 0, 2])
	assert np.allclose(exp_lb, link_labels_py(lb, linkage))
	assert np.allclose(exp_lb, link_labels(lb, linkage))


