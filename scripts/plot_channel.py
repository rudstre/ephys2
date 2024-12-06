'''
Plot a single amplifier channel from an RHD file.

Example usage: 
> # Plot first 2 seconds of the last channel
> python plot_channel.py -i data/sample_rhd_200825_233156.rhd -e 30000 -c 127
'''


if __name__ == '__main__':
	import os
	import matplotlib.pyplot as plt
	from rhd2df import rhd2df
	import argparse

	parser = argparse.ArgumentParser(description='Plot a channel from RHD data.')

	parser.add_argument('-i', '--input', dest='input', type=str, help='RHD input file path', required=True)
	parser.add_argument('-c', '--channel', dest='channel', type=int, help='Channel number', required=True)
	parser.add_argument('-s', '--start', dest='start', type=int, help='Start frame', default=None)
	parser.add_argument('-e', '--end', dest='end', type=int, help='End frame', default=None)

	args = vars(parser.parse_args())

	if not os.path.exists(args['input']):
		raise ValueError(f'Input file {args["input"]} not found')

	df = rhd2df(args['input'], args['start'], args['end'])
	df[args['channel']].plot()
	plt.tight_layout()
	plt.show()

