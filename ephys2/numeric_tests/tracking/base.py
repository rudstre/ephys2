'''
Base benchmarking class for clustering & tracking tasks
'''
from typing import Tuple, Dict, List
from abc import ABC, abstractmethod
import numpy as np
import numpy.typing as npt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch
import colorcet as cc
import scipy.sparse as sp
import os
import pdb
import time

from numeric_tests.utils import *

from ephys2.lib.types import *

class TrackingBenchmark(ABC):

	''' Overrides ''' 

	@abstractmethod
	def get_data_and_ground_truth(self) -> Tuple[npt.NDArray[float], Labeling]:
		'''
		Produce the source data and ground truth (will only be called once)
		'''
		pass

	@abstractmethod
	def perturb_data(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		'''
		Perturb a dataset to measure tracking performance. The locations of the data points should be preserved, in order to use the ground truth.
		'''
		pass

	@abstractmethod
	def run_algorithms(self, 
			X1: npt.NDArray[np.float32], 	# Dataset 1
			X2: npt.NDArray[np.float32]		# Dataset 2 (should be temporally adjacent to 1)
		) -> Dict[str, LinkedLabeling]:
		'''
		Label two time-adjacent datasets and link their labels where possible.
		Both are guaranteed to have the same shape.
		'''
		pass

	@abstractmethod
	def embed_2d(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		'''
		Extract 2d embedding.
		'''
		pass

	'''
	Standard quality metrics for tracking (TODO)
	'''

	

	'''
	Running the benchmark
	'''

	def run(self):
		print('Getting data...')
		X1, y_act = self.get_data_and_ground_truth()
		X2 = self.perturb_data(X1)

		print('Tracking...')
		tic = time.time()
		results = self.run_algorithms(X1, X2)
		N = len(results)
		print('Took {0:0.1f} seconds'.format(time.time() - tic))
		print('Finished.')

		print('Plotting...')

		# Plot embeddings
		fig, axs = plt.subplots(nrows=2, ncols=N+1, sharex=True, sharey=True, figsize=(5*(N+1), 5))
		E1, E2 = self.embed_2d(X1), self.embed_2d(X2)
		lbls = np.unique(y_act)
		Nlbls = lbls.size
		y_act = np.concatenate((y_act, y_act + Nlbls))
		y_act_links = sp.coo_matrix(
			(np.full(Nlbls*2, True), (
				np.concatenate((lbls, lbls + Nlbls)),
				np.concatenate((np.arange(Nlbls), np.arange(Nlbls)))
			)),
			shape=(Nlbls*2, Nlbls)
		).tocsr()
		ground_truth = LinkedLabeling(
			labeling = y_act,
			linkage = y_act_links,
			block_size = X1.shape[0],
			overlap = 0
		)

		def get_ax(r, c):
			if N == 0:
				return axs[r+c]
			else:
				return axs[r][c]

		plot_linkage(fig, get_ax(0,0), get_ax(1,0), E1, E2, ground_truth)
		get_ax(0,0).set_title('Actual')
		get_ax(1,0).set_title('Actual (perturbed)')

		for i, (name, result) in enumerate(results.items()):
			plot_linkage(fig, get_ax(0,i+1), get_ax(1,i+1), E1, E2, result)
			get_ax(0,i+1).set_title(name)
			get_ax(1,i+1).set_title(f'{name} (perturbed)')

		plt.tight_layout()
		plt.show()

def plot_linkage(
		fig,
		ax1, 
		ax2, 
		X1: npt.NDArray[np.float32], 
		X2: npt.NDArray[np.float32], 
		LL: LinkedLabeling
	):
	'''
	Plot a linked labeling.
	'''
	assert X1.shape[1] == X2.shape[1] == 2
	assert X1.shape == X2.shape
	X = np.concatenate((X1, X2), axis=0)
	N = X1.shape[0]
	lb1, lb2 = LL.labeling[:N], LL.labeling[N:] # Labels occur in blocks
	lb1_max = lb1.max()

	ax1.scatter(X1[:,0], X1[:,1], c=get_labeling_colors(lb1), s=3)
	ax2.scatter(X2[:,0], X2[:,1], c=get_labeling_colors(lb2 - lb2.min()), s=3)

	ax1.get_xaxis().set_visible(False)
	ax1.get_yaxis().set_visible(False)
	ax2.get_xaxis().set_visible(False)
	ax2.get_yaxis().set_visible(False)

	li = LL.linkage.tocsc()
	for c in range(li.shape[1]):
		k1, k2 = li.getcol(c).indices
		p, q = X[LL.labeling == k1].mean(axis=0), X[LL.labeling == k2].mean(axis=0)
		# pdb.set_trace()
		coordsA = ax1.transData if k1 <= lb1_max else ax2.transData
		coordsB = ax1.transData if k2 <= lb1_max else ax2.transData
		patch = ConnectionPatch(xyA=(p[0],p[1]), xyB=(q[0],q[1]), coordsA=coordsA, coordsB=coordsB, color='red')
		fig.add_artist(patch)


