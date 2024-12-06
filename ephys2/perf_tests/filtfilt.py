import pdb
import matplotlib.pyplot as plt
import torch
from scipy import signal
from timeit import Timer
from tqdm import tqdm

from ephys2.lib.utils import *
from ephys2.lib.filter import filtfilt_even, make_iir

if __name__ == '__main__':
	torch.autograd.set_grad_enabled(False)

	N_range = np.linspace(100, 100000, 100)

	N_hist = []
	T_hist_scipy = []
	T_hist_scipy_sos = []
	T_hist_torch = []

	b, a = signal.ellip(4, 0.01, 120, 0.125) 
	sos = signal.iirfilter(4, 0.125, rp=0.01, rs=120, btype='lowpass', analog=False, ftype='ellip', output='sos')
	iir =  make_iir(a, b)
	rng = np.random.default_rng()

	for N in tqdm(N_range):
		N = int(N)
		x = rng.standard_normal(N)**3 + 3*rng.standard_normal(N).cumsum()
		x_ = nptt(x).unsqueeze(0)
		f1 = lambda: signal.filtfilt(b, a, x, padlen=N//10, padtype="even")
		f2 = lambda: signal.sosfiltfilt(sos, x, padlen=N//10, padtype="even")
		f3 = lambda: filtfilt_even(x_, iir, N//10)
		N_hist.append(N)
		T_hist_scipy.append(Timer(f1).timeit(number=10))
		T_hist_scipy_sos.append(Timer(f2).timeit(number=10))
		T_hist_torch.append(Timer(f3).timeit(number=10))

	plt.plot(N_hist, T_hist_scipy, label='scipy')
	plt.plot(N_hist, T_hist_scipy_sos, label='scipy_sos')
	plt.plot(N_hist, T_hist_torch, label='torch')
	plt.legend()
	plt.show()