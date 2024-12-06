'''
Test median filter
'''

import pdb
import pytest
import numpy as np
import scipy.signal as signal

from tests.utils import rel_path
from tests.intanutil.read_multi_data_blocks import read_data

import ephys2
import ephys2.pipeline
import ephys2.pipeline.preprocess
import ephys2.pipeline.preprocess.median

from ephys2.lib.types import *


def _do_median_test(cfg: Config, data: np.ndarray, result: np.ndarray):
	stage = ephys2.pipeline.preprocess.median.MedianFilterStage(cfg)
	stage.initialize()
	x = SBatch(data=data, time=np.arange(data.shape[0]), fs=1, overlap=0)
	y = stage.process(x)

	assert np.allclose(result, y.data)

def test_median_0():
	N = 10
	M = 4
	coeffs = np.arange(M)
	x = np.outer(np.ones(N), coeffs)
	y = x - np.median(coeffs)
	_do_median_test({
		'group_size': M,
		'ignore_channels': [],
	},x,y)

def test_median_1():
	N = 10
	M = 8
	coeffs = np.arange(M)
	x = np.outer(np.ones(N), coeffs)
	y = x.copy()
	y[:,:4] = x[:,:4] - np.median(coeffs[:4])
	y[:,4:] = x[:,4:] - np.median(coeffs[4:])
	_do_median_test({
		'group_size': 4,
		'ignore_channels': [],
	},x,y)

def test_median_2():
	N = 10
	M = 8
	coeffs = np.arange(M)
	x = np.outer(np.ones(N), coeffs)
	y = x.copy()
	y[:,:4] = x[:,:4] - np.median(coeffs[[0,1,3]])
	y[:,4:] = x[:,4:] - np.median(coeffs[4:])
	_do_median_test({
		'group_size': 4,
		'ignore_channels': [2],
	},x,y)

def test_median_3():
	N = 10
	M = 8
	coeffs = np.arange(M)
	x = np.outer(np.ones(N), coeffs)
	y = x.copy()
	y[:,:4] = x[:,:4] - np.median(coeffs[[0,1,3]])
	y[:,4:] = x[:,4:] - np.median(coeffs[[5,6,7]])
	_do_median_test({
		'group_size': 4,
		'ignore_channels': [2,4],
	},x,y)

