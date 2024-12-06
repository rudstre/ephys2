'''
IIR filter response tests
'''

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

from ephys2.pipeline.input.rhd2000 import read_rhd_amp


if __name__ == '__main__':

	header, amp_t, amp_data = read_rhd_amp('/Users/anandsrinivasan/dev/fasrc/data/r4_210612_195804.rhd', 1000, 11000)


	# fs = int(1e3)
	# t = np.linspace(0, 1, fs)
	# x = np.sin(2*np.pi*50*t) + np.sin(2*np.pi*150*t) + np.sin(2*np.pi*250*t) + np.random.randn(t.size)/10
	# lo, hi = 100, 200
	# order = 6
	# rp, rs = 0.1, 100
	# ftype = 'ellip'

	fs = header['sample_rate']
	t = np.arange(1000, 11000)
	x = amp_data[:, 0]
	lo, hi = 500, 7500
	order = 4
	rp, rs = 0.2, 100
	ftype = 'ellip'

	sos = signal.iirfilter(
		order,
		(lo,hi),
		rp=rp,
		rs=rs,
		btype='bandpass',
		analog=False,
		ftype=ftype,
		output='sos',
		fs=fs
	)

	y = signal.sosfiltfilt(sos, x, padtype='odd', padlen=100)

	plt.subplot(3, 1, 1)

	plt.plot(t, x, label='Original')
	plt.plot(t, y, label='Filtered')
	plt.ylabel('Amplitude')

	plt.subplot(3,1,2)

	f_x, pxx_x = signal.periodogram(x, fs)
	f_y, pxx_y = signal.periodogram(y, fs)

	plt.plot(f_x, pxx_x, label='Original')
	plt.plot(f_y, pxx_y, label='Filtered')
	plt.ylabel('Power spectrum')

	plt.subplot(3,1,3)

	w, h = signal.sosfreqz(sos, worN=1500)
	db = 20*np.log10(np.maximum(np.abs(h), 1e-5))

	plt.plot(fs * w/(2*np.pi), db)
	plt.ylim(-75, 5)
	plt.grid(True)
	plt.yticks([0, -20, -40, -60])
	plt.ylabel('Filter gain [dB]')

	plt.suptitle(f'{order}-order {ftype} bandpass')

	# plt.subplot(2, 1, 2)
	# plt.plot(w/np.pi, np.angle(h))
	# plt.grid(True)
	# plt.yticks([-np.pi, -0.5*np.pi, 0, 0.5*np.pi, np.pi],
	#            [r'$-\pi$', r'$-\pi/2$', '0', r'$\pi/2$', r'$\pi$'])
	# plt.ylabel('Phase [rad]')
	# plt.xlabel('Normalized frequency (1.0 = Nyquist)')

	plt.show()