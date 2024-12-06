'''
Test consistency between data formats of ephys2
'''
import pdb
import h5py

from tests.utils import *

from ephys2.pipeline.eval import eval_cfg
from ephys2.lib.h5 import *
from ephys2.lib.singletons import global_state

def test_store_snippets():
	'''
	Check that the compression keymap exactly indexes the snippets file
	'''
	cfg = get_cfg('workflows/store_snippets.yaml')
	cfg_spikes = cfg[0]['input.synthetic.mearec.spikes']
	cfg_spikes['templates_file'] = rel_path('data/templates_50_tetrode_18-02-2022_19-52.h5')
	cfg_spikes['ground_truth_output'] = rel_path('data/mr_gt.h5')
	cfg[1]['checkpoint']['file'] = rel_path('data/snippets.h5')

	try:
		eval_cfg(cfg)
		with h5py.File(rel_path('data/snippets.h5'), 'r') as file:
			for s_id in file.keys():
				H5VBatchSerializer.check(file[s_id], full=True)
				s_size = H5VBatchSerializer.get_size(file[s_id])
				assert s_size == int(cfg_spikes['n_samples'])
	finally:
		remove_if_exists(rel_path('data/snippets.h5'))
		remove_if_exists(rel_path('data/mr_gt.h5'))
		global_state.last_h5 = None

def test_store_labeled_snippets():
	'''
	Check that compressed and labeled events have the identical data
	'''
	cfg = get_cfg('workflows/isosplit_label_summarize.yaml')
	cfg_spikes = cfg[0]['input.synthetic.mearec.spikes']
	cfg_spikes['templates_file'] = rel_path('data/templates_50_tetrode_18-02-2022_19-52.h5')
	cfg_spikes['ground_truth_output'] = rel_path('data/mr_gt.h5')
	cfg[1]['checkpoint']['file'] = rel_path('data/snippets.h5')
	cfg[3]['checkpoint']['file'] = rel_path('data/labeled_snippets.h5')
	cfg[5]['checkpoint']['file'] = rel_path('data/summarized_labeled_snippets.h5')

	try:
		eval_cfg(cfg)
		with h5py.File(rel_path('data/labeled_snippets.h5'), 'r') as file:
			assert file.attrs['tag'] == 'LLVMultiBatch'
			H5LLVMultiBatchSerializer.check(file, full=True)
		with h5py.File(rel_path('data/summarized_labeled_snippets.h5'), 'r') as file:
			assert file.attrs['tag'] == 'SLLVMultiBatch'
			H5SLLVMultiBatchSerializer.check(file, full=True)
	finally:
		remove_if_exists(rel_path('data/snippets.h5'))
		remove_if_exists(rel_path('data/labeled_snippets.h5'))
		remove_if_exists(rel_path('data/summarized_labeled_snippets.h5'))
		remove_if_exists(rel_path('data/mr_gt.h5'))
		global_state.last_h5 = None

def test_labeled_snippets_passthrough():
	'''
	Check that compressed and labeled events have the identical data
	'''
	cfg = get_cfg('workflows/isosplit_label_summarize.yaml')
	cfg_spikes = cfg[0]['input.synthetic.mearec.spikes']
	cfg_spikes['templates_file'] = rel_path('data/templates_50_tetrode_18-02-2022_19-52.h5')
	cfg_spikes['ground_truth_output'] = rel_path('data/mr_gt.h5')
	cfg[1]['checkpoint']['file'] = rel_path('data/result.h5')
	cfg[3]['checkpoint']['file'] = rel_path('data/result.h5')
	cfg[5]['checkpoint']['file'] = rel_path('data/result.h5')

	try:
		eval_cfg(cfg)
		with h5py.File(rel_path('data/result.h5'), 'r') as file:
			assert file.attrs['tag'] == 'SLLVMultiBatch'
			H5SLLVMultiBatchSerializer.check(file, full=True)
	finally:
		remove_if_exists(rel_path('data/result.h5'))
		remove_if_exists(rel_path('data/mr_gt.h5'))
		global_state.last_h5 = None
