'''
Test RHD64 aux inputs
'''

import os
import pdb
import numpy as np
import h5py

from tests.utils import *

from ephys2.lib.h5 import *
from ephys2.lib.singletons import global_state
from ephys2.pipeline.eval import eval_cfg

def test_rhd64_aux_full():
	cfg = get_cfg('workflows/rhd64_aux.yaml')

	# Set aux inputs & batch parameters
	rhd_path = rel_path('data/637147781467463722_10k.rhd')
	dio_name = 'test_rhd64_digital_in.h5'
	aio_name = 'test_rhd64_analog_in.h5'
	dio_chs = list(range(16))
	aio_chs = [1,2,3]
	cfg[0]['input.rhd64']['sessions'] = [[rhd_path]]
	cfg[0]['input.rhd64']['aux_channels'][0]['digital_in'] = dio_chs
	cfg[0]['input.rhd64']['aux_channels'][1]['analog_in'] = aio_chs
	cfg[0]['input.rhd64']['aux_channels'][0]['name'] = dio_name
	cfg[0]['input.rhd64']['aux_channels'][1]['name'] = aio_name

	eval_cfg(cfg)

	dio_out_path = rel_path(f'data/session_0_{dio_name}')
	aio_out_path = rel_path(f'data/session_0_{aio_name}')

	try:
		K = 88
		with open(rhd_path, 'rb') as f:
			frames = np.fromfile(f, dtype=np.uint16)
			assert frames.size % K == 0
			
		# Check the digital change times
		exp_dio_data = frames[K-2::K]
		with h5py.File(dio_out_path, 'r') as f:
			for ch in dio_chs:
				assert str(ch) in f
				ch_times = np.diff(exp_dio_data & 1 << ch) > 0
				assert f[str(ch)]['time'].shape[0] == ch_times.sum()

		# Check the analog aux matches
		with h5py.File(aio_out_path, 'r') as f:
			assert f['data'].shape[1] == len(aio_chs)
			for i, n in enumerate(aio_chs):
				j1 = n * K + 9
				skip = 4 * K
				exp_aio_ch = (frames[j1::skip].astype(np.float32) - 32768) * 3.74e-5
				assert np.allclose(f['data'][::4, n-1], exp_aio_ch)

	finally:
		remove_if_exists(dio_out_path)
		remove_if_exists(aio_out_path)