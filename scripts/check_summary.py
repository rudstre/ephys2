if __name__ == '__main__':
	from pathlib import Path
	import h5py
	import sys
	import numpy as np
	import pdb

	path = str(Path(sys.argv[1]).absolute())
	with h5py.File(path, 'r') as f:
		for tetr in f.keys():
			print(f'Checking Tetrode {tetr}...')
			idir = f[tetr]
			N = idir['summary']['time'].shape[0]
			for i in range(N):
				label = idir['summary']['labels'][i]
				indices = idir['summary']['indices'][i]
				indices = indices[indices > -1]
				labels = np.unique(idir['labels'][indices])
				if labels.size != 1:
					print(f'Coarse label {label} has multiple fine labels: {labels}')
					pdb.set_trace()
				elif labels[0] != label:
					print(f'Coarse label {label} has wrong fine label: {labels[0]}')
					pdb.set_trace()
	print('Done.')