'''
Test consistency between old and new linking algorithms
'''

import h5py

from tests.utils import *

from ephys2.pipeline.eval import eval_cfg
from ephys2.lib.h5 import *
from ephys2.lib.singletons import global_state

def test_equivalence():
	'''
	Check that compressed and labeled events have the identical data
	'''
	cfg_snippets = get_cfg('workflows/store_snippets.yaml')
	cfg_snippets_spikes = cfg_snippets[0]['input.synthetic.mearec.spikes']
	cfg_snippets_spikes['templates_file'] = rel_path('data/templates_50_tetrode_18-02-2022_19-52.h5')
	cfg_snippets_spikes['ground_truth_output'] = rel_path('data/mr_gt.h5')
	cfg_snippets[1]['checkpoint']['file'] = rel_path('data/snippets.h5')
	
	cfg_old = get_cfg('workflows/isosplit_label_summarize_old.yaml')
	cfg_spikes_old = cfg_old[0]['load']
	cfg_spikes_old['files'] = [rel_path('data/snippets.h5')]
	cfg_old[2]['checkpoint']['file'] = rel_path('data/labeled_snippets_old.h5')
	cfg_old[4]['checkpoint']['file'] = rel_path('data/summarized_labeled_snippets_old.h5')

	cfg_new = get_cfg('workflows/isosplit_label_summarize_new.yaml')
	cfg_spikes_new = cfg_new[0]['load']
	cfg_spikes_new['files'] = [rel_path('data/snippets.h5')]
	cfg_new[2]['checkpoint']['file'] = rel_path('data/labeled_snippets_new.h5')
	cfg_new[4]['checkpoint']['file'] = rel_path('data/summarized_labeled_snippets_new.h5')

	try:
		global_state.last_h5 = None
		eval_cfg(cfg_snippets)
		global_state.last_h5 = None
		eval_cfg(cfg_old)
		global_state.last_h5 = None
		eval_cfg(cfg_new)
		with h5py.File(rel_path('data/labeled_snippets_old.h5'), 'r') as file_old:
			with h5py.File(rel_path('data/labeled_snippets_new.h5'), 'r') as file_new:
				assert file_old.attrs['tag'] == 'LLVMultiBatch'
				H5LLVMultiBatchSerializer.check(file_old, full=True)
				assert file_new.attrs['tag'] == 'LLVMultiBatch'
				H5LLVMultiBatchSerializer.check(file_new, full=True)
				data_old = H5LLVMultiBatchSerializer.load(file_old)
				data_new = H5LLVMultiBatchSerializer.load(file_new)
				assert data_old == data_new
		with h5py.File(rel_path('data/summarized_labeled_snippets_old.h5'), 'r') as file_old:
			with h5py.File(rel_path('data/summarized_labeled_snippets_new.h5'), 'r') as file_new:
				assert file_old.attrs['tag'] == 'SLLVMultiBatch'
				H5SLLVMultiBatchSerializer.check(file_old, full=True)
				assert file_new.attrs['tag'] == 'SLLVMultiBatch'
				H5SLLVMultiBatchSerializer.check(file_new, full=True)
				data_old = H5SLLVMultiBatchSerializer.load(file_old)
				data_new = H5SLLVMultiBatchSerializer.load(file_new)
				assert data_old == data_new
	finally:
		remove_if_exists(rel_path('data/snippets.h5'))
		remove_if_exists(rel_path('data/mr_gt.h5'))

		remove_if_exists(rel_path('data/labeled_snippets_old.h5'))
		remove_if_exists(rel_path('data/summarized_labeled_snippets_old.h5'))
		remove_if_exists(rel_path('data/labeled_snippets_new.h5'))
		remove_if_exists(rel_path('data/summarized_labeled_snippets_new.h5'))
		global_state.last_h5 = None