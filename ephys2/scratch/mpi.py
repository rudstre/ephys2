'''
MPI utilities for sending & receing Batch
'''

import numpy as np
from mpi4py import MPI 

from ephys2.lib.types import *

def mpi_recv_batch_sync(comm: MPI.Comm, source: int) -> Optional[Batch]:
	'''
	Receive a Batch synchronously & deserialize.

	Order of multi-part message is:
	1. Data exists (bool)
	2. Metadata
		- c: class, int
		- any class-specific fields
	3-N. Data
	'''	
	exists = comm.recv(source=source, tag=0)
	if exists:
		metadata = comm.recv(source=source, tag=0)

		# SBatch
		if metadata['c'] == 0:
			N_channels = metadata['M']
			N_samples = metadata['N']
			time = np.empty(N_samples, dtype=np.int64)
			data = np.empty((N_samples, N_channels), dtype=np.float32)
			comm.Recv([time, MPI.INT64_T], source=source, tag=0)
			comm.Recv([data, MPI.FLOAT], source=source, tag=0)
			return SBatch(
				time = time, 
				data = data, 
				fs = metadata['fs']
			)

		# Events
		elif metadata['c'] == 1:
			keys = metadata['ks']
			N_features = metadata['M']
			size = metadata['s']
			time = np.empty(size, dtype=np.int64)
			data = np.empty((size, N_features), dtype=np.float32)
			comm.Recv([time, MPI.INT64_T], source=source, tag=0)
			comm.Recv([data, MPI.FLOAT], source=source, tag=0)
			start = 0
			times = dict()
			events = dict()
			for key, stop in keys:
				times[key] = time[start:stop]
				events[key] = data[start:stop]
				start = stop
			return Events(
				times = times,
				events = events,
				max_length = metadata['l']
			)

		else:
			raise Exception(f'Worker {comm.Get_rank()} received unknown metadata from {source}: {metadata}')
	return None

def mpi_send_batch_async(comm: MPI.Comm, dest: int, data: Optional[Batch]):
	'''
	Serialize and send a Batch asynchronously.
	'''
	if data is None:
		comm.isend(False, dest=dest, tag=0)
	elif data.size == 0:
		comm.isend(False, dest=dest, tag=0)
	else:
		comm.isend(True, dest=dest, tag=0)

		if data.__class__ is SBatch:
			metadata = {
				'c': 0,
				'M': data.data.shape[1],
				'N': data.data.shape[0],
				'fs': data.fs
			}
			comm.isend(metadata, dest=dest, tag=0)
			comm.Isend(data.time, dest=dest, tag=0)
			comm.Isend(data.data, dest=dest, tag=0)

		elif data.__class__ is Events:
			N_ks = len(data.times)
			ks = [None] * N_ks
			size = 0 
			for i, k in enumerate(data.times):
				size += data.times[k].size
				ks[i] = (k, size)
			N_features = data.events[ks[0][0]].shape[1]
			metadata = {
				'c': 1,
				'ks': ks,
				'M': N_features,
				's': size,
				'l': data.max_length,
			}
			comm.isend(metadata, dest=dest, tag=0)
			time_buf = np.empty(size, dtype=np.int64)
			data_buf = np.empty((size, N_features), dtype=np.float32)
			start = 0
			for key, stop in keys:
				time_buf[start:stop] = data.times[key]
				data_buf[start:stop] = data.events[key]
			comm.Isend(time_buf, dest=dest, tag=0)
			comm.Isend(data_buf, dest=dest, tag=0)

		else:
			raise Exception(f'Worker {comm.Get_rank()} tried to send data of unknown class {data.__class__} to {dest}')
