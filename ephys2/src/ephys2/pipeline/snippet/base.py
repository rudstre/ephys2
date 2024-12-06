'''
Base definitions for snippeting stages
'''

from ephys2.lib.types import *

class SnippetingStage(ProcessingStage):

	def type_map(self) -> Dict[type, type]:
		return {SBatch: VMultiBatch}