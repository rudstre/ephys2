'''
Extract times for individual clustered units from labeled data
'''

from ephys2.lib.types import *

class TimesStage(ProcessingStage):

	@staticmethod
	def name() -> str:
		return 'times'

	def type_map(self) -> Dict[type, type]:
		return {LVMultiBatch: LTMultiBatch}

	def process(self, data: LVMultiBatch) -> LTMultiBatch:
		return LTMultiBatch(items={
			item_id: LTBatch(
				time = item.time,
				labels = item.labels,
				overlap = item.overlap
			) for item_id, item in data.items.items()
		})
