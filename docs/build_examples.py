'''
Build scripts in the examples/ folder to generate the Sphinx gallery
based on YAML configuration files.
'''
import glob
from typing import Callable
import os
import shutil
import yaml
from tqdm import tqdm
import pdb

from autogen_utils import *

from ephys2.lib.types import *
from ephys2.pipeline.stages import ALL_STAGES
from ephys2.validate import get_mem_usage

NTASKS = 32
NTETRODES = 32
NDIM = 256

header = '''
.. _examples-index:

Example gallery
===============

'''

script = '''# -*- coding: utf-8 -*-
"""
{0}

Configuration
-------------

.. code-block:: yaml

{1}

Parameters
----------
{2}

Resource requirements
---------------------
{3}
"""

# import yaml
# import matplotlib.pyplot as plt
# from ephys2.lib.types import *
# from ephys2.pipeline.stages import ALL_STAGES

# with open("{4}", "r") as file:
# 	cfg = yaml.safe_load(file)
# pipeline = Pipeline.parse(cfg, ALL_STAGES, effectful=False)
# names = [stage.name() for stage in pipeline.stages if stage.name() != 'checkpoint']
# fig = plt.figure(figsize=(7.5, 8))
# figheight = len(names) + .5
# fontsize = 12.5
# for i, name in enumerate(names):
# 	fig.text(0.55, (float(len(names)) - 0.5 - i) / figheight,
# 		name,
# 		ha="right",
# 		size=fontsize,
# 		transform=fig.transFigure,
# 		bbox=dict(boxstyle='square', fc="w", ec="k"))
# plt.show()
'''

if __name__ == '__main__':

	# Relevant paths
	cwd = os.path.dirname(__file__)
	gallery_dir = os.path.realpath(os.path.join(cwd, 'examples'))
	yaml_dir = os.path.realpath(os.path.join(os.path.join(cwd, '..'), 'examples'))
	yaml_paths = list(sorted(glob.glob(os.path.join(yaml_dir, '*.yaml'))))

	# Create fresh
	if os.path.isdir(gallery_dir):
		shutil.rmtree(gallery_dir)
	os.mkdir(gallery_dir)

	# Populate with header
	with open(os.path.join(gallery_dir, 'README.rst'), 'w') as file:
		file.write(header)

	# Populate individual example scripts
	for yaml_path in tqdm(yaml_paths):
		yaml_name = os.path.splitext(os.path.basename(yaml_path))[0]
		script_path = os.path.join(gallery_dir, f'plot_{yaml_name}.py')

		# Parse header associated with example
		with open(yaml_path, 'r') as file:
			try:
				cfg = yaml.safe_load(file)
				pipeline = Pipeline.parse(cfg, ALL_STAGES, effectful=False)
				script_header = ''
				file.seek(0)
				line = file.readline()
				while len(line) >= 2 and line[:2] == '# ':
					script_header += line[2:]
					line = file.readline()
				tabbed_yaml_str = ''.join(['\t' + line for line in file.readlines()])
			except:
				print(f'Error in config: {yaml_path}')
				raise

		# Describe properties of pipeline
		params_table = ''
		for stage_name, param_df in pipeline.describe_params():
			params_table += stage_name + '\n'
			params_table += '+' * len(stage_name) + '\n'
			params_table += df_to_rst(param_df, with_index=False) + '\n'
		mem_table = df_to_rst(get_mem_usage(yaml_path, NTASKS, NTETRODES, NDIM), with_index=True)

		# Write script associated with example
		with open(script_path, 'w') as file:
			file.write(
				script.format(
					script_header,
					tabbed_yaml_str,
					params_table,
					mem_table,
					yaml_path
				)
			)
