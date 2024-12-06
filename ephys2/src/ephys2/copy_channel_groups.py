'''
Copy specific channel groups from one file to another.
'''

import h5py
import os

from ephys2.lib.utils import *

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Copy channel groups from one file to another')
	parser.add_argument('-i', '--input', type=str, help='Source filepath', required=True)
	parser.add_argument('-o', '--output', type=str, help='Target filepath', required=True)
	parser.add_argument('-g', '--groups', type=str, help='Channel groups to copy (comma-separated integers)', required=True)
	parser.add_argument('-r', '--repack', action='store_true', help='Repack the output file to reclaim space', default=False)

	args = parser.parse_args()

	assert is_file_readable(args.input), f'{args.input} is not a readable file'
	assert is_file_writeable(args.output), f'{args.output} is not a writeable file'

	in_path = abs_path(args.input)
	out_path = abs_path(args.output)
	repack = False

	with h5py.File(in_path, 'r') as fin:
		with h5py.File(out_path, 'a') as fout:
			print('Validating...')
			groups = args.groups.strip().split(',')

			# Validate data
			for group in groups:
				assert group in fin.keys(), f'Channel {group} not found in {args.input}'
				
			# Validate & copy metadata
			for k, v in fin.attrs.items():
				if k in fout.attrs:
					assert v == fout.attrs[k], f'Metadata mismatch: {k} in {args.input} does not match {args.output}'
				else:
					fout.attrs[k] = v
					
			# Copy channel groups
			for group in groups:
				if group in fout.keys():
					print(f'Overwriting existing channel group {group} in {args.output}...')
					del fout[group]
					repack = True # Repack after deleting to reclaim space
				else:
					print(f'Creating new channel group {group} in {args.output}...')
				fin.copy(str(group), fout)
				
	# Repack if necessary
	if repack:
		if args.repack:
			tmp_path = out_path + '.tmp'
			cmd = f'h5repack -i {out_path} -o {tmp_path}'
			print(f'HDF5 repack requested, running:\t {cmd}')
			print('This may take a while...')
			returncode = os.system(cmd)
			assert returncode == 0, f'h5repack failed with return code {returncode}. Either run manually, or ignore this error, but your output file may be larger.'
			os.replace(tmp_path, out_path)
		else:
			print('HDF5 repack recommended to reduce file size, but not requested. Run with -r to repack.')
	
	print('Done.')