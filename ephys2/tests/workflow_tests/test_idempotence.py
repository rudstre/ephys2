'''
Test idempotence of checkpointing stage
'''

import pdb
import h5py

from tests.utils import *

from ephys2.pipeline.eval import eval_cfg
from ephys2.lib.h5 import *
from ephys2.lib.singletons import global_state

def test_labeling_idempotence():
	'''
	Check that compressed and labeled events have the identical data
	'''
	cfg = get_cfg('workflows/isosplit_idempotence.yaml')
	cfg_spikes = cfg[0]['input.synthetic.mearec.spikes']
	cfg_spikes['templates_file'] = rel_path('data/templates_50_tetrode_18-02-2022_19-52.h5')
	cfg_spikes['ground_truth_output'] = rel_path('data/mr_gt.h5')
	cfg[1]['checkpoint']['file'] = rel_path('data/snippets.h5')
	cfg[3]['checkpoint']['file'] = rel_path('data/labeled_snippets_1.h5')
	cfg[4]['checkpoint']['file'] = rel_path('data/labeled_snippets_2.h5')

	try:
		eval_cfg(cfg)
		with h5py.File(rel_path('data/labeled_snippets_1.h5'), 'r') as file1:
			with h5py.File(rel_path('data/labeled_snippets_2.h5'), 'r') as file2:
				H5LLVMultiBatchSerializer.check(file1, True)
				H5LLVMultiBatchSerializer.check(file2, True)
				result1 = H5LLVMultiBatchSerializer.load(file1)
				result2 = H5LLVMultiBatchSerializer.load(file2)
				assert result1 == result2
	finally:
		remove_if_exists(rel_path('data/snippets.h5'))
		remove_if_exists(rel_path('data/labeled_snippets_1.h5'))
		remove_if_exists(rel_path('data/labeled_snippets_2.h5'))
		remove_if_exists(rel_path('data/mr_gt.h5'))
		global_state.last_h5 = None