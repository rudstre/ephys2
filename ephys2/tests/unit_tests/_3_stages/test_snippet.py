'''
Test snippeting algorithms
'''

import pdb
import pytest
import numpy as np
import scipy.signal as signal

from tests.utils import rel_path
from tests.intanutil.read_multi_data_blocks import read_data

import ephys2
import ephys2.pipeline
import ephys2.pipeline.snippet
import ephys2.pipeline.snippet.fast_threshold

from ephys2.lib.types import *

'''
Accuracy tests of snippeting algorithms
'''

def _do_snippet_test(K: int, tetrode: np.ndarray, snippets: List[np.ndarray], indices: List[int]):
	'''
	Tetrode: N x 4 array
	Snippet: K x 4 array
	index: time it occurs
	K: size of snippet
	'''
	stage = ephys2.pipeline.snippet.fast_threshold.FastThresholdStage({
		'snippet_length': K,
		'detect_threshold': 50,
		'return_threshold': 20,
		'return_samples': 8,
		'n_channels': 4,
	})
	stage.initialize()
	amp_data = SBatch(
		time = np.arange(tetrode.shape[0]),
		data = tetrode,
		fs = 1,
		overlap = 0,
	)
	result = stage.process(amp_data)
	features = result.items['0'].data
	detected = features.reshape((features.shape[0], 4, K))
	detected = np.transpose(detected, (0, 2, 1))
	snippets = np.array(snippets).reshape((len(snippets), K, 4))

	assert np.allclose(detected, snippets)
	assert np.allclose(result.items['0'].time, np.array(indices))

def test_snippet_0():
	K = 64
	i = 112
	tetrode = np.zeros((1000, 4), dtype=np.float32)
	tetrode[i, :] = 100
	snippets = [
		tetrode[i-K//2:i+K//2]
	]
	indices = [i]
	_do_snippet_test(K, tetrode, snippets, indices)

def test_snippet_1():
	K = 64
	i = 112
	tetrode = np.zeros((1000, 4), dtype=np.float32)
	tetrode[i, :] = 100
	tetrode[i+4, :] = 100
	snippets = [
		tetrode[i-K//2:i+K//2]
	]
	indices = [i]

def test_snippet_1b():
	K = 64
	i = 112
	tetrode = np.zeros((1000, 4), dtype=np.float32)
	tetrode[i, :] = 100
	tetrode[i+4, :] = 110
	snippets = [
		tetrode[i+4-K//2:i+4+K//2]
	]
	indices = [i]

def test_snippet_2():
	K = 64
	i = 112
	tetrode = np.zeros((1000, 4), dtype=np.float32)
	tetrode[i, :] = 100
	tetrode[i+9, :] = 100
	snippets = [
		tetrode[i-K//2:i+K//2],
		tetrode[i+9-K//2:i+9+K//2],
	]
	indices = [i,i+9]
	_do_snippet_test(K, tetrode, snippets, indices)

def test_snippet_3():
	K = 64
	i = 112
	tetrode = np.zeros((1000, 4), dtype=np.float32)
	tetrode[i, :] = 40
	snippets = []
	indices = []
	_do_snippet_test(K, tetrode, snippets, indices)

def test_snippet_4():
	K = 64
	i = 112
	tetrode = np.zeros((1000, 4), dtype=np.float32)
	tetrode[i:, :] = 100
	snippets = []
	indices = []
	_do_snippet_test(K, tetrode, snippets, indices)
