'''
Synthetic spike generator (see README.md for details)
'''
from .gen import *
from ephys2.pipeline.benchmark.base import *
from ephys2.pipeline.input.synthetic.utils import *

class MaglandSpikesStage(SyntheticInputStage):

	def parameters() -> Parameters:
		return SyntheticInputStage.parameters() | {
			
		}

	def initialize(self):
		super().initialize()

		# Generate waveform library
