'''
Main entry point for ephys2 (use with mpirun)
'''

import os

''' Disable multithreading (causes oversubscription in workstation environment) ''' 

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import pdb
import yaml
import signal
import sys
import traceback

from ephys2.lib.mpi import MPI, mpi_try
from ephys2.lib.utils import abs_path
from ephys2.pipeline.eval import eval_cfg
from ephys2.lib.singletons import logger, profiler, global_state


def run_pipeline(filepath: str):
	with open(filepath, 'r') as f:
		cfg = yaml.safe_load(f)

	mpi_try(eval_cfg, cfg)

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Ephys2 command-line interface')
	parser.add_argument('cfg', type=str, help='YAML configuration file path')
	parser.add_argument('-v', '--verbose', help='Print debug statements', action='store_true', default=False)
	parser.add_argument('-p', '--profile', help='Run with profiling enabled', action='store_true', default=False)
	parser.add_argument('-d', '--debug', help='Run with deep checks enabled (slow)', action='store_true', default=False)
	args = parser.parse_args()
	varargs = vars(args)

	logger.verbose = args.verbose
	profiler.on = args.profile
	global_state.debug = args.debug

	filepath = abs_path(varargs['cfg'])
	if not os.path.exists(filepath):
		raise ValueError(f'Configuration file {filepath} not found')

	logger.print(f'Running pipeline with configuration file {filepath}')
	run_pipeline(filepath)
