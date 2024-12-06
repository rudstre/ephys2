'''
Test IIR filters
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
import ephys2.pipeline.preprocess.iirfilter

from ephys2.lib.types import *

'''
Accuracy tests of IIR filters against reference Scipy implementations.
'''

def _do_iir_test(cfg: Config):
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
	
	stage = ephys2.pipeline.preprocess.iirfilter.BandpassStage(cfg)
	stage.initialize()
	data = input_stage.produce()
	raw = data.data.copy()
	result1 = stage.process(data)
	result2 = signal.sosfiltfilt(stage.sos.astype(np.float32), raw, axis=0, padtype=cfg['padding_type'], padlen=cfg['padding_length'])

	assert np.allclose(result1.data, result2, atol=1e-2)

def test_iir_0():
	_do_iir_test({
		'order': 4,
		'highpass': 300,
		'lowpass': 7500,
		'Rp': 1,
		'Rs': 100,
		'type': 'ellip',
		'padding_type': 'odd',
		'padding_length': 300,
	})

