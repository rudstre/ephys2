'''
Build scripts in the stages/ folder to generate the Sphinx gallery
based on available stages.
'''
import glob
from typing import Callable
import os
import shutil
import yaml
from tqdm import tqdm
import pdb
from typing import List, Dict

from autogen_utils import *

from ephys2.pipeline.stages import ALL_STAGES
from ephys2.lib.types import *

NTASKS = 32
NTETRODES = 32
NDIM = 256

header = '''
.. _examples-index:

Available processing stages
===========================

'''

script = '''# -*- coding: utf-8 -*-
"""
{0}

Description
-----------
{1}

Parameters
----------
{2}
"""
'''

if __name__ == '__main__':

	# Relevant paths
	cwd = os.path.dirname(__file__)
	gallery_dir = os.path.realpath(os.path.join(cwd, 'stages'))

	# Create fresh
	if os.path.isdir(gallery_dir):
		shutil.rmtree(gallery_dir)
	os.mkdir(gallery_dir)

	# Populate with header
	with open(os.path.join(gallery_dir, 'README.rst'), 'w') as file:
		file.write(header)

	# Populate individual example scripts
	def process_stage(path: List[str], stage: Stage):
		str_path = '.'.join(path)
		assert len(path) >= 1
		if len(path) == 1:
			script_path = os.path.join(gallery_dir, f'plot_{str_path}.py')
		else:
			subfolder = os.path.join(gallery_dir, path[0])
			if not os.path.isdir(subfolder):
				os.mkdir(subfolder)
				with open(os.path.join(subfolder, 'README.rst'), 'w') as file:
					subfolder_header = path[0] + '\n' + ''.join(['-'] * len(path[0]))
					file.write(subfolder_header)
			script_path = os.path.join(subfolder, f'plot_{str_path}.py')

		script_header = str_path + '\n' + (''.join(['='] * len(str_path)))
		params_table = df_to_rst(stage.describe_params(), with_index=False)

		# Write script associated with example
		with open(script_path, 'w') as file:
			file.write(
				script.format(
					script_header,
					stage.description(),
					params_table
				)
			)

	# Process each section of stages
	def process_section(path: List[str], section: Dict):
		for k, v in section.items():
			if type(v) is dict:
				process_section(path + [k], v)
			else:
				process_stage(path + [k], v)

	process_section([], ALL_STAGES)
