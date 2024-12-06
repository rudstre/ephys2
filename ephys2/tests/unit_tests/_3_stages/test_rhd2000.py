'''
Test RHD input
'''

import os
import pytest
import numpy as np
import pdb
import glob

from tests.utils import rel_path
from tests.intanutil.read_multi_data_blocks import read_data

import ephys2
import ephys2.pipeline
import ephys2.pipeline.input
import ephys2.pipeline.input.rhd2000

import ephys2._cpp as _cpp

from ephys2.lib.types import *
from ephys2.lib.utils import *

'''
Accuracy tests of RHD imports against reference Intan implementation.
'''

def _do_rhd_test(cfg: Config):
	stage = ephys2.pipeline.input.rhd2000.RHD2000Stage(cfg)
	stage.initialize()
	try:
		result = stage.produce()
	finally:
		stage.cleanup()

	expected_time, expected_data = [], []
	for f in flatten_list(cfg['sessions']):
		data = read_data(f.path, do_notch_filter=False)
		stop = None if f.stop == np.inf else f.stop
		expected_time.append(result.fs * data['t_amplifier'][f.start:stop])  # Intan does conversion to seconds
		expected_data.append(data['amplifier_data'].T[f.start:stop])

	expected_time = np.concatenate(expected_time)
	expected_data = np.concatenate(expected_data, axis=0)

	# TODO: add tests for global time
	# assert np.allclose(result.time, expected_time), 'Time stream did not match'
	assert np.allclose(result.data, expected_data), 'Amplifier stream did not match'

def test_rhd_full():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_from_beginning():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 0, 1000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_to_end():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 1000, np.inf)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_multi_blocks():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 120 * 4, 120 * 10)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_single_block_right_offset():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 120 * 4, 120 * 4 + 17)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_single_block_left_offset():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 120 * 4 + 12, 120 * 5)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_single_block_both_offset():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 120 * 4 + 10, 120 * 4 + 30)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_multi_block_both_offset():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 120 * 4 + 10, 120 * 7 + 30)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_multifile_full():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd')), RORangedFilePath(rel_path('data/sampledata.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_multifile_left_offset():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd'), 1000, np.inf), RORangedFilePath(rel_path('data/sampledata.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_multifile_right_offset():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/sampledata.rhd')), RORangedFilePath(rel_path('data/sampledata.rhd'), 0, 20000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})

def test_rhd_multifile_pattern():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(f) for f in glob.glob(rel_path('data/sample*.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
	})



