'''
HDF5 utilities
'''
from typing import Any, List, Tuple, Union
from datetime import datetime
import warnings
import h5py 
import math
import json

from ephys2.lib.singletons import logger

'''
Types
'''
H5Dir = Union[h5py.File, h5py.Group, h5py.Dataset] # HDF5 directory
H5ID = Tuple[Union[h5py.h5f.FileID, h5py.h5g.GroupID, h5py.h5d.DatasetID], str]

'''
Functions
'''

def binary_search_interval(ds: h5py.Dataset, elem: Any) -> Tuple[int, int]:
	'''
	Find the indices of the smallest containing interval in a sorted, monotone increasing dataset.
	'''
	if ds.shape[0] == 0:
		warnings.warn('Empty dataset; returning (0, 0)')
		return 0, 0
	lo, hi = 0, ds.shape[0] - 1
	prev_lo, prev_hi = None, None
	while (lo != prev_lo) or (hi != prev_hi):
		prev_lo, prev_hi = lo, hi
		mid = (lo + hi) // 2
		res = (lo + hi) % 2
		val1, val2 = ds[mid], ds[mid+res]

		if val2 <= elem:
			lo = mid + res
		elif val1 <= elem:
			lo = mid
		if val1 >= elem:
			hi = mid
		elif val2 >= elem:
			hi = mid + res
	return lo, hi

class open_h5s:
	def __init__(self, filepaths: List[str], mode: str):
		self.filepaths = filepaths
		self.mode = mode

	def __enter__(self):
		self.files = [h5py.File(f, self.mode) for f in self.filepaths]
		return self.files

	def __exit__(self, exc_type, exc_value, exc_traceback):
		for f in self.files:
			f.close()

def compute_time_offsets(files: List[h5py.File], fs: int) -> List[int]:
	'''
	Compute time offsets based on the existence of metadata
	'''
	start_times = []
	last_start_time = None
	time_offsets = []

	for i, file in enumerate(files):
		start_time = None
		if 'metadata' in file.attrs:
			md = json.loads(file.attrs['metadata'])
			if 'start_time' in md:
				start_time = datetime.fromisoformat(md['start_time'])
		start_times.append(start_time)

		# Calculate offsets between files
		if (start_time != None) and (last_start_time != None):
			dt = (start_time - last_start_time).total_seconds()
			dt = math.ceil(dt * fs)
			dt += time_offsets[-1]
		else:
			dt = 0
		time_offsets.append(dt)
		last_start_time = start_time

	# Validate result
	if any(t != None for t in start_times):
		assert all(t != None for t in start_times), 'Some files contained a start time while others did not.'
		logger.print(f'Start times: {[t.isoformat() for t in start_times]}')
	assert all(t >= 0 for t in time_offsets), 'The loaded files appear to be out-of-order in time. Please check your files.'

	return time_offsets

def h5dir_id(h5dir: H5Dir) -> H5ID:
	return (h5dir.id, h5dir.name)

def create_overwrite_dataset(h5dir: H5Dir, name: str, shape: Tuple[int, ...], **kwargs) -> h5py.Dataset:
	'''
	Create a dataset in the given directory, overwriting any existing dataset with the same name.
	'''
	if name in h5dir:
		del h5dir[name]
		logger.debug('Overwrote', name)
	return h5dir.create_dataset(name, shape, **kwargs)

def create_overwrite_group(h5dir: H5Dir, name: str) -> h5py.Group:
	'''
	Create a group in the given directory, overwriting any existing group with the same name.
	'''
	if name in h5dir:
		del h5dir[name]
		logger.debug('Overwrote', name)
	return h5dir.create_group(name)