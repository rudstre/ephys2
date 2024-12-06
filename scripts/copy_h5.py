import h5py

class open_h5s:
	def __init__(self, filepaths, mode: str):
		self.filepaths = filepaths
		self.mode = mode

	def __enter__(self):
		self.files = [h5py.File(f, self.mode) for f in self.filepaths]
		return self.files

	def __exit__(self, exc_type, exc_value, exc_traceback):
		for f in self.files:
			f.close()

ips = [
	f'/Volumes/olveczky_lab_holy2/Everyone/ForAnand/may3/{i}.h5' for i in [1,2,3]
]
ops = [
	f'/Users/anandsrinivasan/dev/fasrc/data/{i}.h5' for i in [1,2,3]
]

N = 10123

with open_h5s(ips, 'r') as ifs:
	with open_h5s(ops, 'w') as ofs:
		for (ifi, ofi) in zip(ifs, ofs):
			ofi.attrs['metadata'] = ifi.attrs['metadata']
			ofi.attrs['tag'] = ifi.attrs['tag']
			for k in ifi.keys():
				print(k)
				odir = ofi.create_group(k)
				odir.create_dataset('time', data=ifi[k]['time'][:N])
				odir.create_dataset('data', data=ifi[k]['data'][:N])

