import numpy as np
import cProfile
import pstats
import traceback
import h5py
from tqdm import tqdm
from sklearn.decomposition import PCA
import random
import matplotlib.pyplot as plt
import colorcet as cc
import math

from ephys2.lib.isosplit import *

random.seed(0)
np.random.seed(0)

n_trials = 10
N = 100000
M = 10
colors = np.array(cc.glasbey_bw)
show_plot = True

pca = PCA(n_components=M)
pca2 = PCA(n_components=2)

nrows = math.ceil(np.sqrt(n_trials))
ncols = math.ceil(n_trials / nrows)
fig, axs = plt.subplots(nrows=nrows, ncols=ncols)

profiler = cProfile.Profile()

for i in tqdm(range(n_trials)):
	row, col = np.divmod(i, ncols)
	with h5py.File('/Users/anandsrinivasan/dev/fasrc/data/a049_23.h5', 'r') as file:
		size = file['21']['data'].shape[0]
		i = random.randint(N, size - N)
		j = i + N
		data = file['21']['data'][i:j]
		data = pca.fit_transform(data)

		profiler.enable()
		labeling = isosplit5(
			data,
			isocut_threshold = 0.9,
			min_cluster_size = 8,
			K_init = 200,
			refine_clusters = False,
			max_iterations_per_pass = 500,
			random_seed = 0,
			jitter = 0
		)
		profiler.disable()

		data = pca2.fit_transform(data)
		axs[row][col].scatter(data[:, 0], data[:, 1], c=colors[labeling], s=2)

stats = pstats.Stats(profiler).sort_stats('tottime')
stats.print_stats(40)

plt.show()
