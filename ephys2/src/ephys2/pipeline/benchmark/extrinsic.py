'''
Parallelized extrinsic benchmarking stage
'''
import math
import h5py
import numpy as np
import numpy.typing as npt
from typing import Dict, Tuple
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import pdb

from ephys2 import _cpp
from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.singletons import global_metadata, global_state
from ephys2.lib.h5.utils import binary_search_interval
from ephys2.lib.h5 import *
from ephys2.lib.utils import safe_divide
from ephys2.lib.array import *
from ephys2.lib.metrics import *

from .base import *

@dataclass_json
@dataclass
class ExtrinsicBenchmark(Benchmark):
	full_CM: ConfusionMatrix_L # Multiclass confusion matrix
	matched_CM: ConfusionMatrix_L # Confusion matrix for only matched spikes
	pair_CM: ConfusionMatrix_L # Pairwise confusion matrix
	full_accuracy: float 
	matched_accuracy: float 
	precision: List[float] # Per-estimated unit precision
	recall: List[float] # Per-ground truth unit recall
	full_homogeneity: float
	matched_homogeneity: float
	full_completeness: float
	matched_completeness: float
	adj_rand_index: float
	false_positive_rate: int
	false_negative_rate: int
	tag: str = 'ExtrinsicBenchmark'

class ExtrinsicBenchmarksStage(BenchmarksStage):
	fp_label = -1 # False positive label

	@staticmethod
	def name() -> str:
		return 'extrinsic'

	def type_map(self) -> Dict[type, type]:
		return {
			LVMultiBatch: LVMultiBatch,
			LLVMultiBatch: LLVMultiBatch,
			SLLVMultiBatch: SLLVMultiBatch,
		}

	@staticmethod
	def parameters() -> Parameters:
		return BenchmarksStage.parameters() | {
			'ground_truth_data': FileParameter( # No checks on this file, as it may not exist yet
				units = None,
				description = 'File path where ground-truth spike time and label information exists'
			),
			'max_dt_ground_truth': FloatParameter(
				units = 'ms',
				description = 'Maximum interval between a ground-truth and predicted spike to be considered the same',
				start = 0,
				stop = np.inf
			),
		}

	def initialize(self):
		self.CTs = dict() # Entries of contingency tables - access by [chgroup][(GT unit, est unit)]

	def process(self, data: Batch) -> Batch:
		'''
		Match this batch of data to the corresponding region in the ground-truth, and 
		estimate various metrics.

		This assumes the ground-truth and estimated labels have exactly the same metadata:
		# channel groups, sampling rate, etc.
		'''
		max_dt_samples = math.ceil(self.cfg['max_dt_ground_truth'] * global_metadata['sampling_rate'] / 1000)

		with h5py.File(self.cfg['ground_truth_data'], 'r') as gt_file:
			assert gt_file.attrs['tag'] == 'LTMultiBatch'
			for item_id, est_item in data.items.items():

				# Map labels into the linked domain, if needed
				est_labels = est_item.labels
				if issubclass(self.input_type(), LLVMultiBatch):
					est_labels = link_labels(est_labels, est_item.linkage)

				# Initialize local state
				if not (item_id in self.CTs):
					self.CTs[item_id] = dict()

				# Compute aligned ground-truth interval
				gt_chdir = gt_file[item_id]
				if (gt_chdir['time'].shape[0] > 0) and (est_item.size > 0):
					start_idx, _  = binary_search_interval(gt_chdir['time'], est_item.time[0])
					_, stop_idx = binary_search_interval(gt_chdir['time'], est_item.time[-1])
					gt_times = gt_chdir['time'][start_idx:stop_idx]
					gt_labels = gt_chdir['labels'][start_idx:stop_idx]
				else:
					gt_times = np.array([], dtype=np.int64)
					gt_labels = np.array([], dtype=np.int64)
				# Align the ground-truth and estimated sequences
				aligned_labels = _cpp.align_sequences(
					gt_times,
					est_item.time,
					gt_labels,
					est_labels,
					max_dt_samples,
					self.fp_label, # Label for missing data in ground-truth or estimated
				)
				pairs, counts = np.unique(aligned_labels, axis=0, return_counts=True)
				# Update pairwise contingency entries
				for (gt_lbl, est_lbl), count in zip(pairs, counts):
					key = (gt_lbl, est_lbl)
					if not (key in self.CTs[item_id]):
						self.CTs[item_id][key] = 0
					self.CTs[item_id][key] += count

		return data

	def run_benchmark(self) -> ExtrinsicBenchmark:
		all_CTs = self.comm.gather(self.CTs, root=0)

		if self.rank == 0:
			CTs = all_CTs[0]  # Contingency tables
			CMs = dict()      # Confusion matrices
			MCMs = dict()     # Matched confusion matrices
			N_fp = 0
			N_fn = 0
			N_gt = 0
			N_est = 0

			# All CTs have the same outer structure; merge them
			for chgroup in CTs:
				for CTs_ in all_CTs[1:]:
					for key in CTs_[chgroup]:
						if not (key in CTs[chgroup]):
							CTs[chgroup][key] = 0
						CTs[chgroup][key] += CTs_[chgroup][key]

				# Convert to confusion matrices
				CMs[chgroup], MCMs[chgroup], fps, fns, gts, ests = optimal_confusion_matrix(CTs[chgroup], self.fp_label)
				N_fp += fps
				N_fn += fns
				N_gt += gts
				N_est += ests
				
			# Full confusion matrix
			full_CM = square_block_diag(CMs.values())
			full_MCM = square_block_diag(MCMs.values())

			# Compute metrics
			full_accuracy, precision, recall = accuracy_precision_recall(full_CM)
			matched_accuracy, _, __ =  accuracy_precision_recall(full_MCM)
			full_homogeneity, full_completeness = homogeneity_completeness(full_CM)
			matched_homogeneity, matched_completeness = homogeneity_completeness(full_MCM)
			pair_CM = pairwise_confusion(full_CM)
			adj_rand_index = adjusted_rand_index(pair_CM)
			fpr = safe_divide(N_fp, N_est, 0) 
			fnr = safe_divide(N_fn, N_gt, 0)

			return ExtrinsicBenchmark(
				method = self.cfg['method_name'],
				dataset = self.cfg['dataset_name'],
				full_CM = full_CM.tolist(),
				matched_CM = full_MCM.tolist(),
				pair_CM = pair_CM.tolist(),
				full_accuracy = full_accuracy,
				matched_accuracy = matched_accuracy,
				full_homogeneity = full_homogeneity,
				matched_homogeneity = matched_homogeneity,
				full_completeness = full_completeness,
				matched_completeness = matched_completeness,
				adj_rand_index = adj_rand_index,
				false_positive_rate = fpr,
				false_negative_rate = fnr,
				precision = precision.tolist(),
				recall = recall.tolist(),
			)
