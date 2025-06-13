'''
Plot amplifier data from RHD files 

Example usage: 
> # Plot 1 second of data after the 1st second 
> python rhd2df.py -i data/sample_rhd_200825_233156.rhd -o data/sample_rhd_200825_233156.csv -s 30000 -e 60000
'''

if __name__ == '__main__':
	import os
	import pdb	
	import matplotlib.pyplot as plt
	import pandas as pd
	import numpy as np
	import argparse
	import colorcet as cc
	from intanutil.read_multi_data_blocks import read_data

	parser = argparse.ArgumentParser(description='Plot a channel from RHD data.')

	parser.add_argument('-i', '--input', dest='input', type=str, help='RHD input file path', required=True)
	parser.add_argument('-s', '--start', dest='start', type=int, help='Start frame', default=None)
	parser.add_argument('-e', '--end', dest='end', type=int, help='End frame', default=None)

	args = vars(parser.parse_args())

	if not os.path.exists(args['input']):
		raise ValueError(f'Input file {args["input"]} not found')

	data = read_data(args['input'], start=args['start'], stop=args['end'], notch_filter=False)
	chs = data['amplifier_channels']
	ampf, ampf_t = data['amplifier_data'], data['t_amplifier']
	zeros = np.zeros_like(ampf_t)
	N_chips = len(set(ch['board_stream'] for ch in chs))
	N_chs_per_chip = len(set(ch['chip_channel'] for ch in chs))
	fig, axs = plt.subplots(N_chs_per_chip, N_chips)
	for i_ch, ch in enumerate(chs):
		chan = ch['chip_channel']
		chip = ch['board_stream']
		tetr = chan // 4
		axs[chan][chip].plot(ampf_t, zeros, color='black')
		axs[chan][chip].plot(ampf_t, ampf[i_ch], color=cc.glasbey[tetr])
		if chan != N_chs_per_chip-1:
			axs[chan][chip].xaxis.set_visible(False)
		axs[chan][chip].yaxis.set_visible(False)


	plt.tight_layout()
	plt.show()
