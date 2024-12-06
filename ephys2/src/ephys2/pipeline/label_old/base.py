'''
Base abstract stage for labeling & linking.
'''

from typing import Tuple, Dict, Set, FrozenSet
from abc import abstractmethod
import numpy as np
import numpy.typing as npt
import warnings

from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.singletons import global_state
from ephys2.pipeline.link.segfuse import SegfuseStage

class LabelingStage(ProcessingStage):

	def type_map(self) -> Dict[type, type]:
		return {VMultiBatch: LLVMultiBatch}

	@staticmethod
	def parameters() -> Parameters:
		return SegfuseStage.parameters()

	def initialize(self):
		SegfuseStage.initialize(self)

	def process(self, data: VMultiBatch) -> LLVMultiBatch:
		# Check consistency of parameters
		assert not (global_state.last_h5 is None), 'Cannot label data without an HDF5 file. Consider adding a checkpoint stage to your pipeline before the labeling step.'
		assert global_state.load_batch_size == (global_state.load_overlap * 2), 'Labeling step must receive exactly two data blocks, with one overlapping. Please check that batch_size = batch_overlap * 2 in your checkpoint or load stage.'
		assert type(global_state.load_size) is dict, 'Labeling step must receive a dictionary of data sizes'
		block_size = global_state.load_overlap 
		
		items = dict()
		for item_id, item in data.items.items():
			try:
				# Check consistency of all the sizes involved
				assert item.overlap in [0, block_size], 'Overlap must either be 0 or equal to the block size'
				assert item.size >= item.overlap, 'Labeling step must receive items of sizes at least equal to their overlaps'
				assert item.size <= block_size * 2, 'Labeling step must receive items of sizes at most equal to twice the block size'
				block1 = item.data[:block_size]
				block2 = None
				if item.size > block_size:
					block2 = item.data[block_size:]
				labels_start = global_state.load_index - global_state.load_start
				label_space = global_state.load_size[item_id]
				labels, linkage = self.label_and_link(block1, block2, labels_start, label_space)
			except:
				warnings.warn(f'Exception occurred while labeling tetrode {item_id}, has size {item.size} and overlap {item.overlap}')
				raise
			items[item_id] = LLVBatch(
				time = item.time,
				data = item.data,
				overlap = item.overlap,
				labels = labels,
				linkage = linkage,
				block_size = block_size,
				full_links = False
			)
		return LLVMultiBatch(items=items)

	def label_and_link(self, 
			block1: npt.NDArray[np.float32], 
			block2: Optional[npt.NDArray[np.float32]], 
			labels_start: int,
			label_space: int
		) -> Tuple[Labeling, EVIncidence]:
		'''
		Label and link data across two blocks.
		- labels_start provides the start of the label space
		- block_size provides the size of the label block
		- label_space provides the size of the entire label space
		If the second data block is not provided, this method just performs clustering.
		'''
		empty_graph = empty_csr(label_space, dtype=bool)

		# Empty case
		if block1.size == 0:
			return np.zeros(0, dtype=np.int64), empty_graph

		# Cluster 1st block
		block1_y = self.feature_transform(block1)
		block1_labels = self.run_clustering(block1_y) 

		# Offset to position in label space
		block1_labels += labels_start

		# If no second block, just return the labels
		if block2 is None:
			return block1_labels, empty_graph

		# Cluster 2nd block
		assert block2.size > 0, 'Second block must have at least one element'
		block2_y = self.feature_transform(block2)
		block2_labels = self.run_clustering(block2_y) 

		# Offset to position in label space
		block2_labels += labels_start + block1_labels.size 

		# Calculate links
		lc = LinkCandidates(
			block1_labels, 
			block2_labels,
			block1,
			block2,
			label_space
		)
		linkage = SegfuseStage.process(self, lc)

		labels = np.hstack((block1_labels, block2_labels))
		return labels, linkage

	''' Overrides '''

	@abstractmethod
	def feature_transform(self, X: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		'''
		Apply the feature transform prior to clustering.
		'''
		pass

	@abstractmethod
	def run_clustering(self, X: npt.NDArray[np.float32]) -> Labeling:
		'''
		Run clustering on the feature transform of X.
		This method MUST be deterministic; otherwise undefined behavior will occur.
		'''
		pass