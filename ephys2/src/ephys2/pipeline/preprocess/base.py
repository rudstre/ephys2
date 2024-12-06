'''
Base definitions for preprocessing stages
'''

from ephys2.lib.types import *

class PreprocessingStage(ProcessingStage):

	def type_map(self) -> Dict[type, type]:
		return {SBatch: SBatch}