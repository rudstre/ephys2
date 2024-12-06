import os
import h5py
import yaml

from ephys2.lib.types import *

def rel_path(fpath: str) -> str:
	'''
	Get path relative to this directory.
	'''
	return f'{os.path.dirname(os.path.realpath(__file__))}/{fpath}'

def get_cfg(filepath: str):
	with open(rel_path(filepath), 'r') as f:
		return yaml.safe_load(f)

def remove_if_exists(path: str):
	if os.path.exists(path):
		os.remove(path)