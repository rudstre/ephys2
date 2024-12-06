'''
Metrics for spike-sorting quality 
'''

import pdb
import numpy as np
import numpy.typing as npt
from scipy.optimize import linear_sum_assignment
import scipy.sparse as sp
import sklearn.metrics.cluster as skcmetrics
import sklearn.metrics as skmetrics
import scipy.stats as stats
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestNeighbors
from typing import Dict, Tuple, List, Union
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from .utils import *
from .array import *
from .transforms import madev

''' Types ''' 

ContingencyTable = Dict[np.int64, Tuple[np.int64, np.int64]]
ConfusionMatrix = npt.NDArray[np.float32]
ConfusionMatrix_L = List[List[float]] # List version for JSON serialization

@dataclass_json
@dataclass
class SummaryStats:
	''' Summary statistics ''' 
	mean: float
	median: float
	min: float
	max: float
	q1: float
	q3: float

	@staticmethod
	def from_array(arr: Union[List, npt.NDArray]) -> 'SummaryStats':
		if type(arr) is list:
			arr = np.array(arr)
		assert len(arr.shape) == 1
		if arr.size == 0:
			return SummaryStats(
				float('nan'), float('nan'), float('nan'), float('nan'), float('nan'), float('nan')
			)
		else:
			return SummaryStats(
				float(arr.mean()), float(np.median(arr)), float(arr.min()), float(arr.max()), float(np.quantile(arr, 0.25)), float(np.quantile(arr, 0.75))
			)

''' Metrics '''

def optimal_confusion_matrix(CT: ContingencyTable, fp_label: int) -> Tuple[ConfusionMatrix, ConfusionMatrix, float, float, float, float]:
	'''
	Compute a square confusion matrix by solving the linear sum assignment problem.
	Handles the case of fewer units than clusters or vice versa by returning a rectangular argument.
	The matrix columns are ordered according to the unique values in `estimate`.
	Respects the "false-positive" label, such that a false-positive identification can never end up on the diagonal.
	Assumes ground-truth in the rows and estimated in the columns.
	'''
	coords = np.array(list(CT.keys()))
	values = np.array(list(CT.values()))
	if coords.size == 0:
		M = np.empty(dtype=np.int64, shape=(0,0))
		return M, M.copy(), 0, 0, 0, 0

	fps = values[coords[:, 0] == fp_label].sum() # Where ground-truth is self.fp_label
	fns = values[coords[:, 1] == fp_label].sum() # Where estimated is self.fp_label
	gts = values[coords[:, 0] != fp_label].sum()
	ests = values[coords[:, 1] != fp_label].sum()

	# Convert to coordinate form
	rowspace, rows = np.unique(coords[:, 0], return_inverse=True)
	colspace, cols = np.unique(coords[:, 1], return_inverse=True)
	assert rows.shape == cols.shape

	# Get the mask for matched spikes
	mask = np.logical_and(coords[:, 0] != fp_label, coords[:, 1] != fp_label)

	# Create two matrices - one with matched spikes and one with unmatched
	shape = (rowspace.size, colspace.size)
	C_y = sp.coo_matrix((values[mask], (rows[mask], cols[mask])), shape=shape).toarray() # TODO: use sparse?
	C_n = sp.coo_matrix((values[~mask], (rows[~mask], cols[~mask])), shape=shape).toarray()

	# Optimize the matching only over matched spikes
	row_ind, col_ind = linear_sum_assignment(C_y, maximize=True)
	C = (C_y + C_n)[row_ind][:, col_ind]
	MC = C_y[row_ind][:, col_ind]

	# Add back any unmatched columns / rows
	d = row_ind.size
	assert d == min(shape)
	if d < shape[0]: # Unmatched rows
		row_mask = np.full(shape[0], True)
		row_mask[row_ind] = False
		C = np.vstack((C, (C_y + C_n)[row_mask][:, col_ind]))
		MC = np.vstack((MC, C_y[row_mask][:, col_ind]))

	elif d < shape[1]: # Unmatched columns
		col_mask = np.full(shape[1], True)
		col_mask[col_ind] = False
		C = np.hstack((C, (C_y + C_n)[:, col_mask]))
		MC = np.hstack((MC, C_y[:, col_mask]))

	assert C.shape == shape

	return C, MC, fps, fns, gts, ests

def accuracy_precision_recall(C: ConfusionMatrix) -> Tuple[float, npt.NDArray, npt.NDArray]:
	'''
	Compute the accuracy, per-ground-truth label recall, and per-estimated label precision.
	Handles rectangular arguments correctly.
	'''
	C = make_square(C, 0) # Zero-pad to compute precision/recall
	accuracy = safe_divide(np.trace(C), np.sum(C), 0)
	precision = safe_divide(np.diag(C), np.sum(C, axis=1), 0)
	recall = safe_divide(np.diag(C), np.sum(C, axis=0), 0)
	return accuracy, precision, recall

def homogeneity_completeness(C: ConfusionMatrix) -> Tuple[float, float]:
	'''
	Port of SciPy implementation, 
	https://scikit-learn.org/stable/modules/generated/sklearn.metrics.homogeneity_score.html#sklearn.metrics.homogeneity_score
	'''
	MI = skcmetrics.mutual_info_score(None, None, contingency=C)
	gt_entropy = entropy_ax0(C)
	est_entropy = entropy_ax0(C.T)
	homogeneity = safe_divide(MI, gt_entropy, 1)
	completeness = safe_divide(MI, est_entropy, 1)
	return homogeneity, completeness

def entropy_ax0(C: ConfusionMatrix) -> float:
	'''
	Compute the entropy of a clustering along the row-space of a confusion matrix.
	'''
	counts = C.sum(axis=1)
	counts_sum = counts.sum()
	return -np.sum(safe_divide(counts, counts_sum, 0) * (np.log(counts) - np.log(counts_sum)))

def pairwise_confusion(C: ConfusionMatrix) -> ConfusionMatrix:
	'''
	Reduce a multiclass confusion matrix to a pairwise one.
	Port of https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cluster.pair_confusion_matrix.html#:~:text=The%20pair%20confusion%20matrix%20computes,the%20true%20and%20predicted%20clusterings.
	'''
	n_c = C.sum(axis=1)
	n_k = C.sum(axis=0)
	sum_sq = (C ** 2).sum()
	PC = np.empty((2, 2), dtype=np.int64)
	n_samples = C.sum()
	PC[1,1] = sum_sq - n_samples
	PC[0,1] = (C @ n_k).sum() - sum_sq
	PC[1,0] = (C.T @ n_c).sum() - sum_sq
	PC[0,0] = n_samples ** 2 - PC[0,1] - PC[1,0] - sum_sq
	return PC

def adjusted_rand_index(C: ConfusionMatrix) -> float:
	'''
	Calculated adjusted Rand index from a pairwise confusion matrix. 
	Port of https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html#sklearn.metrics.adjusted_rand_score
	'''
	assert C.shape == (2, 2)
	(tn, fp), (fn, tp) = C
	# Special cases: empty data or full agreement
	if fn == 0 and fp == 0:
		return 1.0
	return 2.0 * (tp * tn - fn * fp) / ((tp + fn) * (fn + tn) + (tp + fp) * (fp + tn))

def isolation_distance_and_l_ratio(X_cluster: npt.NDArray, X_other: npt.NDArray) -> Tuple[float, float]:
	'''
	Calculate isolation distance and L-ratio given feature vectors for a cluster and feature vectors in all other clusters.
	Adapted from https://github.com/SpikeInterface/spikeinterface/blob/ce67dd5afcfdc6c450526818ce89c92362ebba4a/spikeinterface/toolkit/qualitymetrics/pca_metrics.py#L128
	'''
	try:
		N = min(X_cluster.shape[0], X_other.shape[0])
		assert N >= 2
		cluster_mean = np.expand_dims(np.mean(X_cluster, 0), 0)
		VI = np.linalg.inv(np.cov(X_cluster, rowvar=False))
		mh_dist = np.sort(cdist(cluster_mean, X_other, 'mahalanobis', VI=VI)[0])
		M = X_cluster.shape[1]
		isolation_distance = mh_dist[N - 1] ** 2
		l_ratio = np.sum(1 - stats.chi2.cdf(mh_dist ** 2, M)) / X_cluster.shape[0]
	except (AssertionError, np.linalg.LinAlgError):
		isolation_distance = np.nan
		l_ratio = np.nan
	return (isolation_distance, l_ratio)

def n_isi_violations(times: npt.NDArray[int], fs_hz: int, ref_period_ms: float) -> int:
	'''
	Number of isi violations for a sequence of times given a sampling rate and refractory period (in ms).
	'''
	if times.size == 0:
		return 0
	return (1000 * np.diff(times / fs_hz) < ref_period_ms).sum()

def n_amp_violations(data: npt.NDArray[float], amp_cutoff: float) -> int:
	'''
	Number of amplitude violations with a given cutoff in the same units as the signal
	'''
	assert len(data.shape) == 2
	return (np.abs(data).max(axis=1) < amp_cutoff).sum()

def firing_rate(times: npt.NDArray[int], fs_hz: int) -> float:
	'''
	Estimate firing rate in Hz from time window
	'''
	if times.size == 0:
		return 0
	return fs_hz * times.size / (times.max() - times.min())

def knn_isolation(
		KNN: NearestNeighbors, 
		cluster_data: npt.NDArray[np.float32], 
		cluster_label: np.int64,
		all_labels: npt.NDArray[np.int64], 
		k: int
	) -> Dict[np.int64, float]:
	'''
	Nearest-neighbors isolation metric based on that used in MountainSort (a simplification), 
	https://www.sciencedirect.com/science/article/pii/S0896627317307456
	KNN: pre-fitted nearest neighbors model
	cluster_data: samples corresponding to a cluster
	cluster_label: label of the cluster
	all_labels: labels of all samples
	'''
	assert k >= 1
	assert len(cluster_data.shape) == 2
	assert len(all_labels.shape) == 1
	k = min(k, cluster_data.shape[0])
	N = all_labels.size
	indices = KNN.kneighbors(cluster_data, n_neighbors=k, return_distance=False)
	return (all_labels[indices] == cluster_label).mean()

def avg_peak_amplitude_and_snr(data: npt.NDArray[np.float32]) -> Tuple[float, float]:
	'''
	Maximum absolute value of the centroid and its SNR
	'''
	assert len(data.shape) == 2
	peak = np.abs(data.mean(axis=0)).max()
	sigma = madev(data, axis=None)
	return (peak, peak / sigma)

