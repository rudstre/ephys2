'''
Utilities for testing H5 serializers/loaders
'''

from typing import Callable, List, Any
import h5py
import os
import random
import pdb

from tests.utils import *

from ephys2.lib.h5 import *
from ephys2.lib.types import *

def do_batch_test(
		Serializer: H5Serializer,
		test_equality: Callable[[Any, Any], bool],
		inputs: List[Any]
	):
	outpath = rel_path('data/test.h5')
	try:
		if Serializer == H5ArraySerializer:
			# Array serializers require top-level name
			serializer = Serializer('data', full_check=True, rank=0, n_workers=1)
		else:
			serializer = Serializer(full_check=True, rank=0, n_workers=1)
		serializer.initialize(outpath)
		for arr in inputs:
			serializer.write(arr)
		if len(inputs) > 0:
			with h5py.File(serializer.get_worker_path(0), 'r') as in_dir:
				for i, result in enumerate(serializer.iter_chunks(in_dir)):
					assert test_equality(inputs[i], result)
	finally:
		remove_if_exists(outpath)
		serializer.cleanup()


def do_reserialize_test(
		Serializer: type,
		Loader: type,
		test_equality: Callable[[Any, Any], bool],
		inputs: List[Any],
		expected: Any,
		npartitions: int,
		start=None,
		stop=None,
		overlap=0,
	):

	assert npartitions >= 1
	outpath = rel_path('data/test_out.h5')
	try:
		if Serializer == H5ArraySerializer:
			# Array serializers require top-level name
			serializers = [Serializer('data', full_check=False, rank=i, n_workers=npartitions) for i in range(npartitions)]
		else:
			serializers = [Serializer(full_check=False, rank=i, n_workers=npartitions) for i in range(npartitions)]
		for ser in serializers:
			ser.initialize(outpath)
			# Set temp paths which would normally be broadcast using MPI
			ser.tmp_path = serializers[0].tmp_path
			ser.filepath = ser.get_worker_path(ser.rank)
		for i, data in enumerate(inputs):
			j = i % npartitions
			serializers[j].write(data)
		# Run first serializer (including post-serialize)
		serializers[0].serialize()
		others = serializers[1:]
		random.shuffle(others)
		for ser in others:
			ser.serialize()
		with h5py.File(outpath, 'r') as outdir:
			if Serializer == H5ArraySerializer:
				# Array serializers require top-level name
				outdir = outdir['data']
			serializers[0].check(outdir, full=True) # Do any post-serialization checks
			result = Loader.load(outdir, start=start, stop=stop, overlap=overlap)
		assert test_equality(result, expected)
	finally:
		remove_if_exists(outpath)
		serializers[0].cleanup()

