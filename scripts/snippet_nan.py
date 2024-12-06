from ephys2.lib.h5 import *
from ephys2 import _cpp
import numpy as np
import pdb

fpath = '/Users/anandsrinivasan/dev/fasrc/data/snippet_nan.h5'
file = h5py.File(fpath, 'r')
time, data = file['time'][:], file['data'][:]

all_times, all_features, max_length = _cpp.snippet_tetrodes(time, data, 64, 50, 20, 8)
assert not any(np.isnan(data).any() for data in all_features), 'first one failed'

i = 0
while True:
	i += 1
	all_times_, all_features_, max_length_ = _cpp.snippet_tetrodes(time, data, 64, 50, 20, 8)
	assert not any(np.isnan(data).any() for data in all_features_), f'nan failed at {i}'
	assert all(np.allclose(x, y) for x, y in zip(all_times, all_times_)), f'times failed at {i}'
	assert all(np.allclose(x, y) for x, y in zip(all_features, all_features_)), f'features failed at {i}'
	assert max_length_ == max_length, f'max_length failed at {i}'
