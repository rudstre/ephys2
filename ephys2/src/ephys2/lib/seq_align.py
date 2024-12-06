'''
Python prototype for seq alignment.
'''
import numpy as np
import pdb

def pair(times1, times2, max_dist):

	N1, N2 = len(times1), len(times2)

	reverse = False
	if N2 < N1:
		times1, times2 = times2, times1
		N1, N2 = N2, N1
		reverse = True

	assert N1 <= N2

	idxs1, idxs2 = [], []

	i1, i2 = 0, 0
	while (i1 < N1 and i2 < N2):
		best_dist = np.abs(times1[i1] - times2[i2])
		best_i2 = i2

		while (i2 < N2 and times2[i2] <= times1[i1]):
			dist = np.abs(times1[i1] - times2[i2])
			if dist < best_dist:
				best_dist = dist
				best_i2 = i2
			i2 += 1

		if best_i2 < N2 and best_dist <= max_dist:
			idxs1.append(i1)
			idxs2.append(best_i2)

		i1 += 1
		i2 = best_i2 + 1

	return (idxs2, idxs1) if reverse else (idxs1, idxs2)

def mergesort_into(arr, times1, vals1, times2, vals2, i1, i2, I1, I2):
	while (i1 < I1 and i2 < I2):
		if times1[i1] <= times2[i2]:
			arr.append((vals1[i1], -1))
			i1 += 1
		else:
			arr.append((-1, vals2[i2]))
			i2 += 1

	while i1 < I1:
		arr.append((vals1[i1], -1))
		i1 += 1

	while i2 < I2:
		arr.append((-1, vals2[i2]))
		i2 += 1

def seq_align(times1, vals1, times2, vals2, max_dist):

	N1, N2 = len(times1), len(times2)

	idxs1, idxs2 = pair(times1, times2, max_dist)
	arr = [] # result

	K = len(idxs1)
	i1, i2 = 0, 0
	for k in range(K):
		I1, I2 = idxs1[k], idxs2[k]
		mergesort_into(arr, times1, vals1, times2, vals2, i1, i2, I1, I2)
		arr.append((vals1[I1], vals2[I2]))
		i1, i2 = I1 + 1, I2 + 1

	mergesort_into(arr, times1, vals1, times2, vals2, i1, i2, N1, N2)

	return np.array(arr)

