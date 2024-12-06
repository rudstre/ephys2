'''
Pre-run validator for ephys2 configurations. 
Will check the pipeline and return information about 
approximate memory usage.
'''

import os
import yaml
import pandas as pd
import numpy as np
import warnings
import pdb

# Settings
from ephys2.lib.settings import global_settings
global_settings.mpi_enabled = False

from ephys2.lib.utils import abs_path
from ephys2.lib.types import *
from ephys2.pipeline.stages import ALL_STAGES
from ephys2.pipeline.checkpoint import *

def get_mem_usage(filepath: str, ntasks: int, ntetrodes: int, ndim: int, multiplier: float=1.5) -> pd.DataFrame:
	with open(filepath, 'r') as f:
		cfg = yaml.safe_load(f)

	pipeline = Pipeline.parse(cfg, ALL_STAGES, effectful=False) # We don't check filepaths until runtime

	def mem_usage_by_type(ty: type, N):
		if issubclass(ty, VMultiBatch):
			return ty.memory_estimate(ntetrodes, N, ndim)
		elif ty == SBatch:
			return SBatch.memory_estimate(N, 4 * ntetrodes)
		else:
			warnings.warn(f'Couldnt estimate memory usage for {ty}, inserting -1')
			return -1

	mem_stages = []
	mem_values = []

	for i, stage in enumerate(pipeline.stages):
		mem = 0
		if 'batch_size' in stage.cfg:
			N = stage.cfg['batch_size']
			mem = mem_usage_by_type(stage.output_type(), N)

		mem_stages.append(f'{i}_{stage.name()}')
		mem_values.append(mem)

	peak_mem = max(mem_values)
	mem_stages = mem_stages + ['peak']
	mem_values = np.array(mem_values + [peak_mem])
	mem_values = multiplier * ntasks * mem_values / (10 ** 9) # Convert to GB
	mem_values = np.round(mem_values, 4)
	column = f'Est. peak memory usage (GB) for {ntetrodes} tetrodes and {ntasks} workers'
	df = pd.DataFrame(data=mem_values, columns=[column], index=mem_stages)
	return df

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Ephys2 command-line interface')
	parser.add_argument('cfg', type=str, help='YAML configuration file path')
	parser.add_argument('-n', '--ntasks', type=int, help='Number of parallel workers', default=32)
	parser.add_argument('-t', '--ntetrodes', type=int, help='Number of tetrodes', default=32)
	parser.add_argument('-d', '--ndim', type=int, help='Dimension of snippets', default=256)

	args = parser.parse_args()
	varargs = vars(args)

	filepath = abs_path(varargs['cfg'])
	if not os.path.exists(filepath):
		raise ValueError(f'Configuration file {filepath} not found')

	df = get_mem_usage(filepath, args.ntasks, args.ntetrodes, args.ndim)
	print(df)