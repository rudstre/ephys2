if __name__ == '__main__':
	import pdb
	import numpy as np
	import matplotlib.pyplot as plt

	from ephys2.pipeline.input.rhd2000 import read_rhd_amp
	# from ephys2.preprocess import bandpass_median
	import ephys2._cpp as _cpp
	# from ephys2.snippet import snippet_threshold
	# from ephys2.plot import plot_tetrodes, plot_tetrode_snippets, plot_snippets

	header, amp_t, amp_data = read_rhd_amp('/Users/anand/Dev/fasrc/ephys2/data/r4_210612_195804.rhd', 1e6, 1e6+5e4)

	a_l, a_h = 20, 50 # Thresholds in uV
	thr = (a_l, a_h)

	# plot_tetrodes(amp_t, amp_data[:,:8], thr)

	# amp_data = bandpass_median(
	# 	amp_data, 
	# 	4,
	# 	300,
	# 	7500,
	# 	header['sample_rate'],
	# 	3000,
	# 	64
	# )

	print('Preprocessing finished')

	# plot_tetrodes(amp_t, amp_data[:,:8], thr)

	group_times, group_snippets, max_length = _cpp.snippet_tetrodes(
		amp_t,
		amp_data.astype(np.float32),
		64,
		a_h,
		a_l,
		8
	)

	print('Snippetting finished')

	pdb.set_trace()

	# idx = w_tetr <= 1 # plotting the 2 tetrodes

	# plot_tetrode_snippets(amp_t, w_t[idx], w_tetr[idx], w_data[idx], 2)

	# plot_snippets(w_data[:8, :64], thr)

	# plt.show()