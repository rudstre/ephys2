import numpy as np
import numpy.typing as npt
from typing import Tuple, Dict
import time
import os

import ephys2.lib.intanutil.header as iheader
import ephys2.lib._cpp as _cpp

def read_rhd_amp(fpath: str, start_sample: int=0, stop_sample: int=np.inf) -> Tuple[Dict, np.ndarray, np.ndarray]:
	'''
	Read amplifier data from Intan RHD2000 data file format
	See https://intantech.com/files/Intan_RHD2000_data_file_formats.pdf 

	Parallelization set by environment variable OMP_NUM_THREADS.

	stop_sample = inf indicates all data.
	'''
	assert int(start_sample)==start_sample, 'Pass integral start time'
	start_sample = int(start_sample)
	assert start_sample >= 0, 'Start time must be nonnegative'
	assert stop_sample == np.inf or int(stop_sample)==stop_sample, 'Pass integral stop time'
	if stop_sample != np.inf:
		stop_sample = int(stop_sample)
	assert stop_sample > start_sample, 'Stop time must occur after start time'

	tic = time.time()

	if not os.path.exists(fpath):
		raise ValueError(f'{fpath} does not exist.')

	filesize = os.path.getsize(fpath)
	with open(fpath, 'rb') as f:
		header = iheader.read_header(f)
		header_offset = f.tell()
	bytes_per_block = iheader.get_bytes_per_data_block(header)
	bytes_after_amp = iheader.get_bytes_after_amp(header)
	samples_per_block = header['num_samples_per_data_block']
	num_blocks = int((filesize - header_offset) / bytes_per_block)
	n_channels = header['num_amplifier_channels']

	# print(f'Version major: {header["version"]["major"]}, minor: {header["version"]["minor"]}')

	# Validate data range
	num_samples = num_blocks * samples_per_block
	stop_sample = num_samples if stop_sample == np.inf else stop_sample

	if not (start_sample <= stop_sample <= num_samples):
		raise ValueError(f'Requested samples {start_sample} to {stop_sample}, but only {num_samples} total are available.')

	# Read blocks
	amp_t, amp_data = _cpp.read_rhd2000_batch(
		fpath, 
		header_offset, 
		bytes_per_block, 
		bytes_after_amp,
		samples_per_block, 
		start_sample, 
		stop_sample, 
		n_channels
	)

	print('Done!  Elapsed time: {0:0.1f} seconds'.format(time.time() - tic))

	return header, amp_t, amp_data