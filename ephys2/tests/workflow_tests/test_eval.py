'''
Test that various pipelines can be run.
'''

import os
import pdb

from tests.utils import *

from ephys2.lib.singletons import global_state
from ephys2.pipeline.eval import eval_cfg

def test_copy_rhd():
	cfg = get_cfg('workflows/copy_rhd.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [[rel_path('data/sampledata.rhd')]]
	cfg[1]['checkpoint']['file'] = rel_path('data/copy_rhd.h5')

	try:
		eval_cfg(cfg)
	finally:
		remove_if_exists(rel_path('data/copy_rhd.h5'))
		global_state.last_h5 = None

def test_snippet():
	cfg = get_cfg('workflows/snippet.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [[rel_path('data/sampledata.rhd')]]
	cfg[3]['checkpoint']['file'] = rel_path('data/snippets.h5')

	try:
		eval_cfg(cfg)
	finally:
		remove_if_exists(rel_path('data/snippets.h5'))
		global_state.last_h5 = None

def test_aux_outputs():
	cfg = get_cfg('workflows/rhd_aux.yaml')
	cfg[0]['input.rhd2000']['sessions'] = [[rel_path('data/r4_210612_195804_part.rhd')]]
	cfg[1]['checkpoint']['file'] = rel_path('data/snippets.h5')

	try:
		eval_cfg(cfg)
	finally:
		remove_if_exists(rel_path('data/snippets.h5'))
		remove_if_exists(rel_path('data/session_0_test_digital_in.h5'))
		remove_if_exists(rel_path('data/session_0_test_analog_in.h5'))
		global_state.last_h5 = None
