import h5py
import matplotlib.pyplot as plt
import pdb
import numpy as np

fpath = '/Volumes/olveczky_lab_holy2/Anand/data/kh_all/session_0_digital_in.h5'

with h5py.File(fpath, 'r') as file:
	time, labels = file['15']['time'][:], file['15']['labels'][:]

assert time.size == labels.size

def inflate(change_times, change_labels, start, stop):
	assert start <= stop
	idx_start = np.argmax(change_times >= start)
	idx_stop = np.argmax(change_times >= stop)
	sig_time = np.arange(start, stop)
	sig_values = np.full(stop-start, 0)
	subtimes = change_times[idx_start:idx_stop].astype(np.intp)
	sublabels = change_labels[idx_start:idx_stop].astype(np.intp).copy()
	sublabels[sublabels == 0] = -1
	sig_values[subtimes - start] = sublabels
	sig_values = np.cumsum(sig_values)
	sig_values -= min(0, sig_values.min())
	assert sig_time.shape == sig_values.shape
	return sig_time, sig_values

N = 1000000
start = time[0] - 100
sig_times, sig_values = inflate(time, labels, start, start + N)

plt.plot(sig_times, sig_values)
plt.tight_layout()
plt.show()