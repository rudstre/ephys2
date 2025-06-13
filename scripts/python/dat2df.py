'''
Extract amplifier data from DAT files as CSV-formatted DataFrame for quick-and-dirty processing and analysis.

Example usage: 
> # Get 1 second of data after the 1st second 
> python rhd2df.py -i data/amplifier.data -o data/amplifier.csv -s 30000 -e 60000
'''

import os
import pdb
import pandas as pd
import numpy as np

from intanutil.read_multi_data_blocks import read_data

def rhd2df(fp: str, start: int, stop: int) -> pd.DataFrame:
	data = read_data(fp, start=start, stop=stop)
	df = pd.DataFrame(
		data=data['amplifier_data'].T,
		index=data['t_amplifier'],
		columns=[ch['custom_order'] for ch in data['amplifier_channels']],
	)
	return df

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Extract RHD segments as CSV.')

	parser.add_argument('-i', '--input', dest='input', type=str, help='RHD input file path', required=True)
	parser.add_argument('-o', '--output', dest='output', type=str, help='CSV output file path', required=True)
	parser.add_argument('-s', '--start', dest='start', type=int, help='Start frame', default=None)
	parser.add_argument('-e', '--end', dest='end', type=int, help='End frame', default=None)

	args = vars(parser.parse_args())

	if not os.path.exists(args['input']):
		raise ValueError(f'Input file {args["input"]} not found')

	df = rhd2df(args['input'], args['start'], args['end'])
	df.to_csv(args['output'])
	print(f'Wrote {args["output"]}')

