'''
Test that various pipelines agree with ground-truth data.
'''

import os
import pdb
import numpy as np
import h5py

from tests.utils import *
from tests.intanutil.read_multi_data_blocks import read_data

from ephys2.pipeline.eval import eval_cfg
from ephys2.lib.loader import SBatchLoader
from ephys2.lib.h5 import *
from ephys2.pipeline.input.rhd64 import RHD64Stage
from ephys2.lib.singletons import global_state

def test_copy_rhd():
	rhd_path = rel_path('data/sampledata.rhd')
	cfg = get_cfg('workflows/copy_rhd.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [[rhd_path]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd.h5')	

	eval_cfg(cfg)

	expected = read_data(rhd_path)
	with h5py.File(rel_path('data/copy_rhd.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

	assert np.allclose(expected['amplifier_data'].T, result.data), 'Amplifier stream did not match'
	remove_if_exists(rel_path('data/copy_rhd.h5'))
	global_state.last_h5 = None

def test_copy_rhd64():
	rhd_path = rel_path('data/637196011466866173_part.rhd')
	cfg = get_cfg('workflows/copy_rhd64.yaml')
	cfg[0]['input.rhd64']['sessions'] = [[rhd_path]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd64.h5')	

	eval_cfg(cfg)

	stage = RHD64Stage({
		'sessions': [[RORangedFilePath(rhd_path)]],
		'start': 0,
		'stop': np.inf,
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	})
	stage.initialize()
	expected = stage.produce()
	with h5py.File(rel_path('data/copy_rhd64.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

	assert expected == result
	remove_if_exists(rel_path('data/copy_rhd64.h5'))
	global_state.last_h5 = None

def test_copy_rhd_multi():
	rhd_path = rel_path('data/sampledata.rhd')
	cfg = get_cfg('workflows/copy_rhd.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [[rhd_path, rhd_path]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd.h5')	

	eval_cfg(cfg)

	expected = read_data(rhd_path)
	with h5py.File(rel_path('data/copy_rhd.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

	expected_data = np.concatenate((expected['amplifier_data'].T, expected['amplifier_data'].T), axis=0)

	assert np.allclose(expected_data, result.data), 'Amplifier stream did not match'
	remove_if_exists(rel_path('data/copy_rhd.h5'))
	global_state.last_h5 = None

def test_copy_rhd_multi_2():
	rhd_path = rel_path('data/sampledata.rhd')
	cfg = get_cfg('workflows/copy_rhd.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [[
		{
			'path': rhd_path,
			'start': 1000,
			'stop': 2000,
		},
		{
			'path': rhd_path,
			'start': 1000,
			'stop': np.inf,
		},
		rhd_path
	]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd.h5')	

	eval_cfg(cfg)

	expected = read_data(rhd_path)
	with h5py.File(rel_path('data/copy_rhd.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

	expected_data = np.concatenate((
		expected['amplifier_data'].T[1000:2000], 
		expected['amplifier_data'].T[1000:],
		expected['amplifier_data'].T
	), axis=0)

	assert np.allclose(expected_data, result.data), 'Amplifier stream did not match'
	remove_if_exists(rel_path('data/copy_rhd.h5'))
	global_state.last_h5 = None

def test_copy_rhd64_multi():
	rhd_path = rel_path('data/637196011466866173_part.rhd')
	cfg = get_cfg('workflows/copy_rhd64.yaml')
	cfg[0]['input.rhd64']['sessions'] = [[rhd_path, rhd_path]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd64.h5')	

	eval_cfg(cfg)

	stage = RHD64Stage({
		'sessions': [[RORangedFilePath(rhd_path), RORangedFilePath(rhd_path)]],
		'start': 0,
		'stop': np.inf,
		'batch_size': np.inf,
		'batch_overlap': 0,
		'sampling_rate': 30000,
		'datetime_pattern': '*',
		'aux_channels': [],
	})
	stage.initialize()
	expected = stage.produce()
	with h5py.File(rel_path('data/copy_rhd64.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

	assert expected == result
	remove_if_exists(rel_path('data/copy_rhd64.h5'))
	global_state.last_h5 = None

def test_copy_rhd_pattern():
	cfg = get_cfg('workflows/copy_rhd.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [rel_path('data/*sampledata.rhd')]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd.h5')	

	eval_cfg(cfg)

	expected = read_data(rel_path('data/sampledata.rhd'))
	with h5py.File(rel_path('data/copy_rhd.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

	assert np.allclose(expected['amplifier_data'].T, result.data), 'Amplifier stream did not match'
	remove_if_exists(rel_path('data/copy_rhd.h5'))
	global_state.last_h5 = None

def test_copy_ofps():
	ofps_path = rel_path('data/sample_ofps')
	cfg = get_cfg('workflows/copy_ofps.yaml')
	cfg[0]['input.intan_ofps']['sessions'] = [[ofps_path]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_ofps.h5')	

	eval_cfg(cfg)

	with h5py.File(rel_path('data/copy_ofps.h5'), 'r') as f:
		loader = SBatchLoader(0, 1, 0, np.inf, np.inf, 0)
		result = loader.load(f)

		N, M = result.data.shape[0], result.data.shape[1]
		expected = 0.195 * np.fromfile(f'{ofps_path}/amplifier.dat', dtype=np.int16, count=N*M).astype(np.float32)
		expected.shape = (N, M)

	assert np.allclose(expected, result.data), 'Amplifier stream did not match'
	remove_if_exists(rel_path('data/copy_ofps.h5'))
	global_state.last_h5 = None

def xtest_copy_dh():
	dh_path = rel_path('data/zenodo_chunk')
	cfg = get_cfg('workflows/copy_dh.yaml')
	cfg[0]['input.synthetic.dhawale.spikes']['directory'] = dh_path
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_dh.h5')	

	eval_cfg(cfg)

	with h5py.File(rel_path('data/copy_dh.h5'), 'r') as f:
		result = H5VMultiBatchSerializer.load(f)

	times_path = rel_path('data/zenodo_chunk/ChGroup_0/SpikeTimes')
	spikes_path = rel_path('data/zenodo_chunk/ChGroup_0/Spikes')
	act_time = np.fromfile(times_path, dtype=np.uint64, count=1000, offset=0).astype(np.int64)
	act_data = np.fromfile(spikes_path, dtype=np.int16, count=1000*64*4, offset=0).astype(np.float32) * 0.195
	act_data.shape = (1000, 64 * 4)

	assert np.allclose(result['0'].time, act_time)
	assert np.allclose(result['0'].data, act_data)

	remove_if_exists(rel_path('data/copy_dh.h5'))
	global_state.last_h5 = None
