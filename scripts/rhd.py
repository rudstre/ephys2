if __name__ == '__main__':
	import pdb
	import matplotlib.pyplot as plt
	import numpy as np

	from ephys2.pipeline.input.rhd2000 import read_rhd_amp
	from ephys2.plot import plot_tetrodes

	header, amp_t, amp_data = read_rhd_amp('/Users/anand/Dev/fasrc/ephys2/data/r4_210612_195804.rhd', 1000, np.inf)

	pdb.set_trace()

	a_l, a_h = 20, 50 # Thresholds in uV

	plot_tetrodes(amp_t, amp_data[:,:32], (a_l, a_h))

	plt.show()