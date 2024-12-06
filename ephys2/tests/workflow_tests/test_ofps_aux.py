'''
Test OFPS aux input
'''

import os
import pdb
import numpy as np
import h5py

from tests.utils import *

from ephys2.lib.h5 import *
from ephys2.lib.singletons import global_state
from ephys2.pipeline.eval import eval_cfg

def test_ofps_aux_full():
	cfg = get_cfg('workflows/ofps_aux.yaml')

	# Set aux inputs & batch parameters
	dio_name = 'test_ofps_digital_in.h5'
	aio_name = 'test_ofps_analog_in.h5'
	dio_chs = [12, 13, 14, 15]
	aio_chs = [1, 2, 3, 4, 5, 6]
	cfg[0]['input.intan_ofps']['sessions'] = [[rel_path('data/sample_ofps')]]
	cfg[0]['input.intan_ofps']['aux_channels'][0]['digital_in'] = dio_chs
	cfg[0]['input.intan_ofps']['aux_channels'][1]['analog_in'] = aio_chs
	cfg[0]['input.intan_ofps']['aux_channels'][0]['name'] = dio_name
	cfg[0]['input.intan_ofps']['aux_channels'][1]['name'] = aio_name

	eval_cfg(cfg)

	dio_out_path = rel_path(f'data/sample_ofps/session_0_{dio_name}')
	aio_out_path = rel_path(f'data/sample_ofps/session_0_{aio_name}')

	try:
		dio_path = rel_path('data/sample_ofps/digitalin.dat')
		exp_dio_data = np.fromfile(dio_path, dtype=np.uint16)

		# Check the digital change times
		with h5py.File(dio_out_path, 'r') as f:
			for ch in dio_chs:
				assert str(ch) in f
				ch_times = np.diff(exp_dio_data & 1 << ch) > 0
				assert f[str(ch)]['time'].shape[0] == ch_times.sum()

		aio_path = rel_path('data/sample_ofps/auxiliary.dat')
		exp_aio_data = 0.0000374 * np.fromfile(aio_path, dtype=np.uint16).astype(np.float32)
		exp_aio_data.shape = (10000, 6)

		# Check the analog aux matches
		with h5py.File(aio_out_path, 'r') as f:
			assert np.allclose(f['data'][:], exp_aio_data)

	finally:
		remove_if_exists(dio_out_path)
		remove_if_exists(aio_out_path)