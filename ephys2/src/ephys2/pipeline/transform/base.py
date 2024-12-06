'''
Base definitions for feature transform stages
'''

from ephys2.lib.types import *

class TransformStage(ProcessingStage):

	def type_map(self) -> Dict[type, type]:
		return {VMultiBatch: VMultiBatch}
