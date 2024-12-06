'''
Utilities
'''
import os
from typing import Tuple, Callable, Any, Optional, List, Iterable
from pathlib import Path
import numpy as np
import numpy.typing as npt
import uuid
from itertools import cycle, islice, chain
import dataclasses
import pdb

def abs_path(fpath: str) -> str:
	'''
	Platform-independent absolute path
	'''
	return str(Path(fpath).absolute())

def ext_mul(x: float, y: float) -> float:
	'''
	Multiply the extended real numbers. (convention: 0 x inf = 0)
	'''
	if x == 0 or y == 0:
		return 0
	return x*y

def roundrobin(iterables):
	'''
	Round-robin cycle through iterables, from itertools recipe:
	https://docs.python.org/3/library/itertools.html#recipes
	'''
	num_active = len(iterables)
	nexts = cycle(iter(it).__next__ for it in iterables)
	while num_active:
		try:
			for next in nexts:
				yield next()
		except StopIteration:
			# Remove the iterator we just exhausted from the cycle.
			num_active -= 1
			nexts = cycle(islice(nexts, num_active))

def uuid_to_np(u: uuid.UUID) -> npt.NDArray[np.int64]:
	'''
	Array-friendly UUID type 
	stored as 6 np.int64 scalars
	'''
	return np.array(u.fields, dtype=np.int64)

def np_to_uuid(arr: npt.NDArray[np.int64]) -> uuid.UUID:
	'''
	Convert back from 6-integer 64-bit int array to UUID
	'''
	return uuid.UUID(fields=arr.tolist())

def split_dict_by(d: dict, fun: Callable[[Any, Any], bool]) -> Tuple[dict, dict]:
	'''
	Split a dictionary according to a condition, returning one satisfying and the other not.
	'''
	return (
		{k: v for k, v in d.items() if fun(k, v)},
		{k: v for k, v in d.items() if not fun(k, v)}
	)

def dict_sym_dif(d1: dict, d2: dict) -> Tuple[dict, dict]:
	'''
	Take the symmetric difference of two dicts (by key), returning (1) their intersection and (2) their symmetric difference
	'''
	dint = {k: (d1[v], d2[v]) for k, v in d1.items if k in d2}
	df1 = {k: v for k, v in d1.items if not (k in d2)}
	df2 = {k: v for k, v in d2.items if not (k in d1)}
	return dint, (df1 | df2)

def dataclass_items(object):
	'''
	Get the items of a dataclass instance as key-value pairs.
	'''
	return {
		f.name: getattr(object, f.name)
		for f in dataclasses.fields(object)
	}

def safe_divide(a, b, default):
	c = a / b
	c = np.nan_to_num(c, nan=default, posinf=default, neginf=default)
	return c

def is_file_writeable(filepath: str) -> bool:
	'''
	Non-destructive check if a location is writeable. 
	Taken from https://www.novixys.com/blog/python-check-file-can-read-write/
	'''
	if os.path.exists(filepath):
		# path exists
		if os.path.isfile(filepath): # is it a file or a dir?
			# also works when file is a link and the target is writable
			return os.access(filepath, os.W_OK)
		else:
			return False # path is a dir, so cannot write as a file
			# target does not exist, check perms on parent dir
	pdir = os.path.dirname(filepath)
	if not pdir: pdir = '.'
	# target is creatable if parent dir is writable
	return os.access(pdir, os.W_OK)

def is_file_readable(filepath: str) -> bool:
	'''
	Non-destructive file readability check.
	'''
	try:
		with open(filepath, 'r') as f:
			return True
	except:
		return False

def is_dir_readable(Directory: str) -> bool:
	return (
		os.path.isdir(Directory) and
		os.access(Directory, os.R_OK)
	)

def is_dir_writeable(Directory: str) -> bool:
	return (
		os.path.isdir(Directory) and
		os.access(Directory, os.W_OK)
	)

def flatten_list(xs: list) -> list:
	return list(chain.from_iterable(xs))

def lca_path(paths: Iterable[str], effectful: bool=True) -> str:
	'''
	Find lowest common ancestor of multiple filepaths
	'''
	path_parts = [Path(abs_path(p)).parts for p in paths]
	assert len(path_parts) > 0
	root = path_parts[0][0]
	assert all(parts[0] == root for parts in path_parts), 'filesystem must have a single root'
	out_path = Path(root)
	n = min(len(parts) for parts in path_parts)
	for i in range(1, n):
		node = path_parts[0][i]
		if all(parts[i] == node for parts in path_parts):
			out_path /= node
		else:
			break
	out_path = str(out_path)
	if effectful and os.path.isfile(out_path):
		out_path = os.path.dirname(out_path)
	return out_path

