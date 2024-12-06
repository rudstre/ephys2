'''
Test zeroing
'''

import pdb
import pytest
import numpy as np
import scipy.signal as signal
from typing import List

from tests.utils import rel_path
from tests.intanutil.read_multi_data_blocks import read_data

import ephys2
import ephys2.pipeline
import ephys2.pipeline.preprocess
import ephys2.pipeline.preprocess.zero

from ephys2.lib.types import *


def _do_zero_test(chs: List[int], data: np.ndarray, result: np.ndarray):
	stage = ephys2.pipeline.preprocess.zero.SetZeroStage({'channels': chs})
	stage.initialize()
	x = SBatch(data=data, time=np.arange(data.shape[0]), fs=1, overlap=0)
	y = stage.process(x)

	assert np.allclose(result, y.data)

def test_zero_0():
	N = 10
	M = 4
	coeffs = np.arange(M)
	x = np.outer(np.ones(N), coeffs)
	y = x.copy()
	y[:,2] = 0
	_do_zero_test([2],x,y)

def test_zero_1():
	N = 10
	M = 4
	coeffs = np.arange(M)
	x = np.outer(np.ones(N), coeffs)
	y = x.copy()
	y[:,2:] = 0
	_do_zero_test([2,3],x,y)
