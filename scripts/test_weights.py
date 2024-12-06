import numpy as np
from ephys2.pipeline.label_old.spc_segfuse import *

def calc_link_weight(
		c1: npt.NDArray, 								# Centroid 1
		c2: npt.NDArray, 								# Centroid 2
		sig_s: float,										# Sigmoid slope
		sig_k: float,  									# Sigmoid offset
	) -> float:
	'''
	Calculate a link's weight by rescaled distance between centroids.
	'''
	# First rescale the centroids (not documented in paper, but see FAST source)
	ka = max(c1.max(), c2.max())
	kb = max(c1.min(), c2.min())
	c1 = (c1 - ka) / (kb - ka)
	c2 = (c2 - ka) / (kb - ka)
	# Distance between rescaled centroids
	d = np.sqrt(np.linalg.norm(c1 - c2) / c1.size)
	# Scaled distance
	a = np.exp(-(d - sig_k) / sig_s)
	return a / (1 + a)


sig_s = 0.005
sig_k = 0.03

N1 = 10
N2 = 20
M = 100

X1 = np.random.randn(N1, M).astype(np.float32)
X2 = np.random.randn(N2, M).astype(np.float32)

D_1 = np.zeros((N1, N2))
for i, x1 in enumerate(X1):
	for j, x2 in enumerate(X2):
		D_1[i, j] = calc_link_weight(x1, x2, sig_s, sig_k)

D_2 = calc_link_weights(X1, X2, sig_s, sig_k)

print(D_1.dtype)
print(D_2.dtype)

assert np.allclose(D_1, D_2)