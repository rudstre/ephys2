'''
Input stages with ground-truth information
'''
import h5py
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional

from ephys2.lib.types import *
from ephys2.lib.singletons import logger
from .base import *

class GroundTruthInputStage(ParallelInputStage, ABC):
	'''
	Input with ground-truth data.
	Note that batch_size is measured in input units (as is usual).
	(E.g. an input signal containing an arbitrary number of grond-truth events.)
	'''

	@staticmethod
	def parameters() -> Parameters:
		prms = ParallelInputStage.parameters() | {
			'ground_truth_output': RWFileParameter(
				units = None,
				description = 'File path to which ground-truth spike time and label information will be written'
			),
		}
		del prms['batch_overlap'] # Cannot use a batch_overlap with ground-truth data generator, for now.
		return prms

	def initialize(self):
		self.cfg['batch_overlap'] = 0
		super().initialize()
		logger.print(f'Writing ground-truth to {self.cfg["ground_truth_output"]}...')
		self.write_ground_truth(self.metadata, self.cfg['ground_truth_output'])
		logger.print('Finished.')

	@abstractmethod
	def write_ground_truth(self, md: InputMetadata, path: RWFilePath):
		'''
		Write ground-truth data to the output file. 
		Barrier() will be called afterward.
		'''
		pass

