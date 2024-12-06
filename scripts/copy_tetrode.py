if __name__ == '__main__':
	import argparse
	import h5py 

	parser = argparse.ArgumentParser(description='Copy tetrode data from one session to another')
	parser.add_argument('-i', '--input', type=str, help='Source filepath')
	parser.add_argument('-o', '--output', type=str, help='Target filepath')
	parser.add_argument('-t', '--tetrode', type=int, help='Tetrode number')

	args = parser.parse_args()
	
	with h5py.File(args.input, 'r') as fin:
		with h5py.File(args.output, 'w') as fout:
			fout.attrs['tag'] = fin.attrs['tag']
			fout.attrs['version'] = fin.attrs['version']
			fout.attrs['metadata'] = fin.attrs['metadata']
			fin.copy(str(args.tetrode), fout)

	print('Done')