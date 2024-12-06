'''
Test OFPS aux input
'''

import numpy as np

from ephys2.lib.types import *
from ephys2.lib.utils import *
from ephys2.pipeline.input.intan_ofps import IntanOfpsStage

from tests.utils import *
from tests.unit_tests._3_stages.test_ofps import _do_ofps_test

def test_ofps_full_with_aux():
	_do_ofps_test({
		'sessions': [[RangedDirectory(rel_path('data/sample_ofps'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [
		{
			'analog_in': [1, 2, 3, 4, 5, 6],
			'name': 'ofps_analog_in.h5',
			'downsample': 1
		}, 
		{
			'digital_in': [12, 13, 14, 15],
			'name': 'ofps_digital_in.h5',
		}],
	})

def test_ofps_multisession_with_aux():
	_do_ofps_test({
		'sessions': [[
			RangedDirectory(rel_path('data/sample_ofps'), 100, np.inf),
			RangedDirectory(rel_path('data/sample_ofps'), 0, 5000)
		]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [
		{
			'analog_in': [1, 2, 3, 4, 5, 6],
			'name': 'ofps_analog_in.h5',
			'downsample': 1
		}, 
		{
			'digital_in': [12, 13, 14, 15],
			'name': 'ofps_digital_in.h5',
		}],
	})



