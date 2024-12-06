'''
Test OFPS input
'''

import os
import pytest
import numpy as np
import pdb
import glob

from tests.utils import rel_path

import ephys2
import ephys2.pipeline
import ephys2.pipeline.input
import ephys2.pipeline.input.intan_ofps

import ephys2._cpp as _cpp

from ephys2.lib.types import *
from ephys2.lib.utils import *

'''
Accuracy tests of Intan OFPS imports.
'''

def _do_ofps_test(cfg: Config):
	stage = ephys2.pipeline.input.intan_ofps.IntanOfpsStage(cfg)
	stage.initialize()

	try:
		got_data = stage.produce()
	finally:
		stage.cleanup()

	exp_time, exp_data = [], []
	for md in stage.all_metadata:
		_time, _data = _cpp.read_intan_ofps_batch(
			md.time_path,
			md.amp_path,
			0, 
			md.size,
			md.n_channels
		)
		stop = None if md.stop == np.inf else md.stop
		exp_time.append(_time[md.start:stop])
		exp_data.append(_data[md.start:stop])
	exp_time = np.concatenate(exp_time, axis=0)
	exp_data = np.concatenate(exp_data, axis=0)

	# TODO: add tests for global time
	# assert np.allclose(got_data.time, exp_time), 'Time stream did not match' 
	assert np.allclose(got_data.data, exp_data), 'Amplifier stream did not match'

def test_ofps_full():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_ofps_from_beginning():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps'), 0, 1000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_ofps_to_end():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps'), 1000, np.inf)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_ofps_multi_full():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps')), RangedDirectory(rel_path('data/sample_ofps'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_ofps_multi_from_beginning():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps')), RangedDirectory(rel_path('data/sample_ofps'), 0, 5000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_ofps_multi_middle():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps'), 6000, np.inf), RangedDirectory(rel_path('data/sample_ofps'), 0, 2500)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_ofps_multi_to_end():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps'), 1000, np.inf), RangedDirectory(rel_path('data/sample_ofps'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})