'''
Test decimation
'''

import pdb
import pytest
import numpy as np
import scipy.signal as signal

from tests.utils import rel_path
from tests.intanutil.read_multi_data_blocks import read_data

import ephys2
import ephys2.pipeline
import ephys2.pipeline.input
import ephys2.pipeline.input.rhd2000
import ephys2.pipeline.preprocess
import ephys2.pipeline.preprocess.decimate

from ephys2.lib.types import *


def _do_decimate_test(cfg: Config):
	input_stage = ephys2.pipeline.input.rhd2000.RHD2000Stage({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'))]],
		'start': 1000,
		'stop': 11000,
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})
	input_stage.initialize()
	
	stage = ephys2.pipeline.preprocess.decimate.DecimateStage(cfg)
	stage.initialize()
	data = input_stage.produce()
	result = stage.process(data.copy())
	assert data.fs == result.fs * cfg['factor']
	assert data.size == result.size * cfg['factor']
	assert result.size == result.data.shape[0]

def test_decimate_0():
	_do_decimate_test({
		'order': 4,
		'factor': 4,
		'type': 'iir',
	})

