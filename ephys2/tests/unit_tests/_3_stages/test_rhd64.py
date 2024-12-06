'''
Test FAST RHD64 input
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
import ephys2.pipeline.input.rhd64

import ephys2._cpp as _cpp

from ephys2.lib.types import *

'''
Accuracy tests of FAST-format RHD64 imports 
'''

def _do_rhd64_test(cfg: Config, expected_size: int):
	stage = ephys2.pipeline.input.rhd64.RHD64Stage(cfg)
	stage.initialize()
	data = stage.produce()
	assert data.size == expected_size

def test_rhd64_full():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 10000)

def test_rhd64_from_beginning():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 0, 1000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 1000)

def test_rhd64_to_end():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 1000, np.inf)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 9000)

def test_rhd64_part():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 1034, 5275)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 5275 - 1034)

def test_rhd64_multifile_full():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd')), RORangedFilePath(rel_path('data/637196011466866173_part.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 20000)

def test_rhd64_multifile_left_offset():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 1000, np.inf), RORangedFilePath(rel_path('data/637196011466866173_part.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 19000)

def test_rhd64_multifile_right_offset():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd')), RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 0, 9000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 19000)

def test_rhd64_multifile_both_offset():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 1824, np.inf), RORangedFilePath(rel_path('data/637196011466866173_part.rhd'), 0, 8958)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 18958 - 1824)

def test_rhd64_multifile_pattern():
	_do_rhd64_test({
		'sessions': [[RORangedFilePath(f) for f in glob.glob(rel_path('data/637196011466866173*.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	}, 10000)

