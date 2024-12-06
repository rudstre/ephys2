'''
Test RHD2000 aux inputs
'''

import numpy as np

from ephys2.lib.types import *
from ephys2.lib.utils import *
from ephys2.pipeline.input.rhd2000 import RHD2000Stage
import ephys2._cpp as _cpp

from tests.utils import rel_path
from tests.unit_tests._3_stages.test_rhd2000 import _do_rhd_test
from tests.intanutil.read_multi_data_blocks import read_data


def test_rhd_full_with_aux():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/r4_210612_195804_part.rhd'))]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [{
			'analog_in': [1, 2, 3, 4, 5, 6],
			'name': 'r4_analog_in.h5',
			'downsample': 1000
		}, {
			'digital_in': [15],
			'name': 'r4_digital_in.h5',
		}],
	})

def test_rhd_multi_blocks_with_aux():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/r4_210612_195804_part.rhd'), 118, 543)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [{
			'analog_in': [1, 2, 3, 4, 5, 6],
			'name': 'r4_analog_in.h5',
			'downsample': 1000
		}, {
			'digital_in': [15],
			'name': 'r4_digital_in.h5',
		}],
	})

def test_rhd_multifile_with_aux():
	_do_rhd_test({
		'sessions': [[RORangedFilePath(rel_path('data/r4_210612_195804_part.rhd'), 100, np.inf), RORangedFilePath(rel_path('data/r4_210612_195804_part.rhd'), 0, 20000)]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
		'aux_channels': [{
			'analog_in': [1, 2, 3, 4, 5, 6],
			'name': 'r4_analog_in.h5',
			'downsample': 1000
		}, {
			'digital_in': [15],
			'name': 'r4_digital_in.h5',
		}],
	})

def do_aux_test(fpath: RORangedFilePath):
	stage = RHD2000Stage({
		'sessions': [[fpath]],
		'batch_size': np.inf,
		'batch_overlap': 0,
		'datetime_pattern': '*',
		'aux_channels': [],
		'aux_channels': [{
			'analog_in': [1, 2, 3, 4, 5, 6],
			'name': 'r4_analog_in.h5',
			'downsample': 1000
		}, {
			'digital_in': [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
			'name': 'r4_digital_in.h5',
		}],
	})
	stage.initialize()
	stage.cleanup()
	md = stage.all_metadata[0]
	_, amp_data, analog_data, digital_data = _cpp.read_rhd2000_batch(
		md.path, 
		md.header_offset, 
		md.bytes_per_block, 
		md.bytes_after_amp,
		md.samples_per_block, 
		md.start, 
		md.stop, 
		md.n_channels,
		md.n_analog_channels,
		md.digital_in_enabled
	)
	expected = read_data(md.path, do_notch_filter=False)
	exp_analog_data = np.repeat(expected['aux_input_data'].T, 4, axis=0)
	assert np.allclose(analog_data, exp_analog_data[md.start:md.stop]) 
	for i in range(md.header['num_board_dig_in_channels']):
		ch = md.header['board_dig_in_channels'][i]['native_order']
		digital_data_ch = (digital_data & 1 << ch) > 0
		assert np.allclose(digital_data_ch, expected['board_dig_in_data'][i][md.start:md.stop]) 

def test_aux_full():
	do_aux_test(RORangedFilePath(
		path = rel_path('data/r4_210612_195804_part.rhd'),
		start = 0,
		stop = np.inf
	))

def test_aux_start_offset():
	do_aux_test(RORangedFilePath(
		path = rel_path('data/r4_210612_195804_part.rhd'),
		start = 123,
		stop = np.inf
	))

def test_aux_stop_offset():
	do_aux_test(RORangedFilePath(
		path = rel_path('data/r4_210612_195804_part.rhd'),
		start = 0,
		stop = 4270
	))

def test_aux_both_offset():
	do_aux_test(RORangedFilePath(
		path = rel_path('data/r4_210612_195804_part.rhd'),
		start = 118,
		stop = 5720
	))