'''
Consistency tests of synthetic data generator
'''
import pdb
import numpy as np

from ephys2.pipeline.input.synthetic.mearec.spikes import *
from ephys2.lib.h5.ltbatch import *

from tests.utils import *

def make_standard_MR_generator(rank: int, n_workers: int, cfg: Config=dict()):
	stage = MearecSpikesStage({
		'templates_file': rel_path('data/templates_50_tetrode_18-02-2022_19-52.h5'),
		'n_tetrodes': 1,
		'n_units_per_tetrode': 8,
		'min_firing_rate': 0.1,
		'max_firing_rate': 1.0,
		'refractory_period': 1.5,
		'sampling_rate': 20000,
		'n_samples': 10000,
		'batch_size': 100,
		'batch_overlap': 0,
		'noise_std': 0.0,
		'seed': 0,
	} | cfg)
	stage.rank = rank
	stage.n_workers = n_workers
	stage.initialize()
	return stage

def do_consistency_test(n_workers: int, n_batches: int, cfg=dict()):
	assert n_workers > 0
	assert n_batches > 0

	gt_serial_out = rel_path('data/gt_serial.h5')
	gt_parallel_out = rel_path('data/gt_parallel.h5')

	serial = make_standard_MR_generator(0, 1, cfg | {'ground_truth_output': gt_serial_out})
	parallel = []
	for rank in range(n_workers):
		worker = make_standard_MR_generator(rank, n_workers, cfg | {'ground_truth_output': gt_parallel_out})
		parallel.append(worker)

	serial_result = serial.produce()
	parallel_result = parallel[0].produce()
	for i in range(1, n_batches):
		serial_result.append(serial.produce())
		parallel_result.append(parallel[i % n_workers].produce())

	try:
		assert serial_result == parallel_result

		with h5py.File(gt_serial_out, 'r') as gt_serial:
			with h5py.File(gt_parallel_out, 'r') as gt_parallel:
				d1 = H5LTMultiBatchSerializer.load(gt_serial)
				d2 = H5LTMultiBatchSerializer.load(gt_parallel)
				assert d1 == d2
	finally:
		remove_if_exists(gt_serial_out)
		remove_if_exists(gt_parallel_out)

def test_1_tetrode():
	do_consistency_test(5, 10)

def test_k_tetrode():
	do_consistency_test(4, 13, cfg={'n_tetrodes': 4})

def xtest_k_tetrode_overlap():
	# TODO: fix batch overlap in synthetic data generator
	do_consistency_test(4, 13, cfg={'n_tetrodes': 4, 'batch_overlap': 20})