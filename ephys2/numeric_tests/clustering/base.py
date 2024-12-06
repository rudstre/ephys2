'''
Base benchmarking class for clustering tasks
'''
from typing import Tuple, Dict, List
from abc import ABC, abstractmethod
import numpy as np
import numpy.typing as npt
import pandas as pd
import matplotlib.pyplot as plt
import colorcet as cc
import os
import pdb
import time

import sklearn
import sklearn.metrics
import sklearn.metrics.cluster

from numeric_tests.utils import *

from ephys2.lib.types import *

class ClusterBenchmark(ABC):

	''' Overrides ''' 

	@abstractmethod
	def get_data_and_ground_truth(self) -> Tuple[npt.NDArray[float], Labeling]:
		'''
		Produce the source data and ground truth (will only be called once)
		'''
		pass

	@abstractmethod
	def run_algorithms(self, X: npt.NDArray[float]) -> Dict[str, Labeling]:
		'''
		Cluster a dataset of size (N_samples, M_features) and return an unsigned integer array of cluster assignments (N_samples,)
		for each algorithm. Name of the algorithm indexes the map of returned clusterings.
		'''
		pass

	@abstractmethod
	def embed_2d(self, X: npt.NDArray[float]) -> npt.NDArray[float]:
		'''
		Extract 2d embedding.
		'''
		pass

	'''
	Standard quality metrics for clustering
	'''

	def quality_metrics(self, X: npt.NDArray[float], y_act: npt.NDArray[int], y_est: npt.NDArray[int]) -> pd.DataFrame:
		C = sklearn.metrics.cluster.pair_confusion_matrix(y_act, y_est)
		df = pd.DataFrame.from_dict({
			'Pair confusion 00': [
				C[0][0],
				'[0, inf)',
				'Pairs not clustered together by both assignments',
			],
			'Pair confusion 01': [
				C[0][1],
				'[0, inf)',
				'Pairs clustered together by ground-truth but not prediction',
			],
			'Pair confusion 10': [
				C[1][0],
				'[0, inf)',
				'Pairs clustered together by prediction but not ground-truth',
			],
			'Pair confusion 11': [
				C[1][1],
				'[0, inf)',
				'Pairs clustered together by both assignments',
			],
			'Adjusted mutual information': [
				sklearn.metrics.cluster.adjusted_mutual_info_score(y_act, y_est),
				'[0, 1]',
				'Mutual information of cluster assignments, adjusted for chance'
			],
			'Adjusted Rand index': [
				sklearn.metrics.cluster.adjusted_rand_score(y_act, y_est),
				'[0, 1]',
				'Similarity of cluster assignments, adjusted for chance'
			],
			# 'Calinski-Harabasz score': [
			# 	sklearn.metrics.cluster.calinski_harabasz_score(X, y_est),
			# 	'[0, inf)',
			# 	'Ratio of inter-cluster variance to intra-cluster variance'
			# ],
			'Homogeneity': [
				sklearn.metrics.cluster.homogeneity_score(y_act, y_est), 
				'[0, 1]',
				'Each cluster contains only members of a single class'
			],
			'Completeness': [
				sklearn.metrics.cluster.completeness_score(y_act, y_est),
				'[0, 1]',
				'All members of a given class are assigned to the same cluster'
			],
			'Fowlkes-Mallows index': [
				sklearn.metrics.cluster.fowlkes_mallows_score(y_act, y_est), 
				'[0, 1]',
				'Geometric mean of the pairwise precision and recall'
			],
			'Silhouette coefficient': [
				sklearn.metrics.cluster.silhouette_score(X, y_est),
				'[-1, 1]',
				'Ratio of cluster cohesion to separation'
			],

		}, orient='index', columns=[
			'Value',
			'Range',
			'Meaning'
		])
		df.index.name = 'Metric'
		return df


	'''
	Running the benchmark
	'''

	def run(self):
		print('Getting data...')
		data, y_act = self.get_data_and_ground_truth()

		print('Clustering...')
		clusterings = self.run_algorithms(data)
		N = len(clusterings)
		print('Finished.')

		print('Plotting...')
		metrics_df = None
		for i, (name, y_est) in enumerate(clusterings.items()):
			if metrics_df is None:
				metrics_df = self.quality_metrics(data, y_act, y_est).rename(columns={'Value': name})
			else:
				df = self.quality_metrics(data, y_act, y_est)
				metrics_df.insert(i, name, df['Value'])

		# Plot quality metrics
		show_df(metrics_df)

		# Plot embeddings
		fig, axs = plt.subplots(nrows=1, ncols=N+1, figsize=(5*(N+1), 5))
		embedding = self.embed_2d(data)
		axs[0].set_title('Actual')
		axs[0].scatter(embedding[:,0], embedding[:,1], c=get_labeling_colors(y_act), s=3)
		axs[0].axis('off')

		for i, (name, y_est) in enumerate(clusterings.items()):
			axs[i+1].set_title(name)
			axs[i+1].scatter(embedding[:,0], embedding[:,1], c=get_labeling_colors(y_est), s=3)
			axs[i+1].axis('off')

		plt.tight_layout()
		plt.show()


