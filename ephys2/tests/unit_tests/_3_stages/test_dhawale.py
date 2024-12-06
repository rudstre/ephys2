'''
Consistency tests of Zenodo synthetic data recording
'''
import pdb
import numpy as np
import random
import pytest

from ephys2.pipeline.input.dhawale.spikes import *

from tests.utils import *

def make_standard_dh_generator(cfg: Config=dict(), **kwargs):
	return DhawaleSpikesStage({
		'start': 0,
		'stop': np.inf,
		'batch_size': np.inf,
		'batch_overlap': 0,
		'directory': rel_path('data/zenodo_chunk'),
		'channel_groups': [0],
	} | cfg, **kwargs)

def do_consistency_test(n_workers: int, cfg=dict()):
	assert n_workers > 0

	serial = make_standard_dh_generator()
	parallel = []
	batch_size = 1000 // n_workers
	for rank in range(n_workers):
		worker = make_standard_dh_generator({'batch_size': batch_size}, rank=rank, n_workers=n_workers)
		parallel.append(worker)

	serial_result = serial.produce()
	parallel_result = parallel[0].produce()
	i = 1
	while True:
		data = parallel[i % n_workers].produce()
		if not (data is None):
			parallel_result.append(data)
			i += 1
		else:
			break

	assert serial_result == parallel_result

	times_path = rel_path('data/zenodo_chunk/ChGroup_0/SpikeTimes')
	spikes_path = rel_path('data/zenodo_chunk/ChGroup_0/Spikes')
	act_time = np.fromfile(times_path, dtype=np.uint64, count=1000, offset=0).astype(np.int64)
	act_data = np.fromfile(spikes_path, dtype=np.int16, count=1000*64*4, offset=0).astype(np.float32) * 0.195
	act_data.shape = (1000, 64 * 4)
	assert np.allclose(serial_result['0'].time, act_time)
	assert np.allclose(serial_result['0'].data, act_data)

def xtest_1_worker():
	do_consistency_test(1)

@pytest.mark.repeat(3)
def xtest_k_workers():
	k = random.randint(2, 10)
	do_consistency_test(k)