import h5py
from pydmd import DMD, MrDMD, HODMD
import matplotlib.pyplot as plt
import pdb
import numpy as np
import math
from sklearn.decomposition import PCA
import pywt

i, j = 1000, 1025
n = j - i

with h5py.File('/Users/anandsrinivasan/dev/fasrc/data/a049_23.h5', 'r') as file:
	data = file['21']['data'][i:j]

def plot_eigs(dmd, ax):
	unit_circle = plt.Circle((0.0, 0.0), 1.0, color='green', fill=False, linestyle='--')
	ax.add_artist(unit_circle)
	ax.plot(dmd.eigs.real, dmd.eigs.imag, 'bo', markersize=2)
	ax.set_xlim((-1, 1))
	ax.set_ylim((-1, 1))

def plot_modes(dmd, ax):
	for mode in dmd.modes.T:
		ax.plot(mode)

def plot_reconstruction(y, z, title):
	assert y.shape == z.shape
	nrows = math.ceil(np.sqrt(n))
	ncols = math.ceil(n / nrows)
	fig, axs = plt.subplots(nrows, ncols)
	for idx in range(n):
		r, c = np.divmod(idx, ncols)
		axs[r, c].plot(y[idx], color='blue')
		axs[r, c].plot(z[idx], color='orange')
		axs[r, c].axis('off')
	# fig.suptitle(title)

def plot_pca(y):
	fig, ax = plt.subplots()
	pca = PCA(n_components=2)
	z = pca.fit_transform(y)
	ax.scatter(y[:, 0], y[:, 1], s=2)

k = data.shape[1] // 4
y_ = data.reshape((n, 4, k)).reshape((n * 4, k))

# # Method 1: Higher-order DMD

# dmd = HODMD(svd_rank=0, opt=True, exact=True, d=2)
# dmd.fit(y_)
# z_ = dmd.reconstructed_data.real
# z = z_.reshape((n, 4, k)).reshape((n, 4 * k))
# plot_reconstruction(data, z, 'Higher-order dynamic mode decomposition')

# # Method 2: Truncated wavelet

# level = 2
# coeffs = pywt.wavedec(y_, 'sym3', mode='zero', level=level, axis=1)
# thresh = 9 * np.sqrt(2 * np.log(y_.shape[1]))
# for i in range(len(coeffs)):
# 	coeffs[i] = pywt.threshold(coeffs[i], value=thresh)
# z_ = pywt.waverec(coeffs, 'sym3', mode='zero', axis=1)
# z = z_.reshape((n, 4, k)).reshape((n, 4 * k))
# plot_reconstruction(data, z, 'Truncated wavelet transform (two-level)')

# Method 3: Wavelet without detail

# cA, cD = pywt.dwt(y_, 'sym2', mode='zero', axis=1)
# M = cA.shape[1]
# # cA[:, M//2:] = 0
# z_ = pywt.idwt(cA, np.zeros_like(cD), 'sym2', mode='zero', axis=1)
# z = z_.reshape((n, 4, k)).reshape((n, 4 * k))
# plot_reconstruction(data, z, 'Wavelet-denoised waveforms')

# Method 4: Basis pursuit 

from cr.sparse import lop
# import cr.sparse.cvx.l1ls as l1ls
# from cr.sparse.cvx.adm import yall1
import jax.numpy as jnp
# import cvxpy as cp

# DWT_op = lop.to_matrix(lop.dwt(k, wavelet='db2', level=1)).__array__()
# coeffs = cp.Variable(y_.T.shape)
# alpha = 0.1
# problem = cp.Problem(
# 	cp.Minimize(alpha*cp.norm1(coeffs) + cp.norm2(DWT_op @ y_.T - coeffs)**2),
# )
# # problem = cp.Problem(
# # 	cp.Minimize(cp.norm2(DWT_op @ y_.T - coeffs)**2)
# # )
# problem.solve(verbose=True)
# # pdb.set_trace()
# coeffs = coeffs.value
# # coeffs[k // 4:] = 0
# z_ = (DWT_op.T @ coeffs).T
# z = z_.reshape((n, 4, k)).reshape((n, 4 * k))
# plot_reconstruction(data, z, 'Basis pursuit wavelet denoising')

# Method 5: Beta-weighted truncated wavelet transform 

import scipy.stats as stats


beta = 10
z_ = y_ * stats.beta.pdf(np.linspace(0, 1, k), beta, beta)
cA, cD = pywt.dwt(z_, 'sym2', mode='zero', axis=1)
M = cA.shape[1]
# cA[:, M//2:] = 0
z_ = pywt.idwt(cA, np.zeros_like(cD), 'sym2', mode='zero', axis=1)
z = z_.reshape((n, 4, k)).reshape((n, 4 * k))
plot_reconstruction(data, z, f'Beta-weighted denoised waveforms (beta={beta})')

plt.tight_layout()
plt.show()