'''
Clamp data between high and low values
'''

import numpy as np

from ephys2.lib.types import *

class ClipStage(ProcessingStage):

	@staticmethod
	def name() -> str:
		return 'clip'

	@staticmethod
	def parameters() -> Parameters:
		return {
			'high': FloatParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Upper threshold at which to clip input'
			),
			'low': FloatParameter(
				start = -np.inf,
				stop = 0,
				units = None,
				description = 'Lower threshold at which to clip input'
			),
		}

	def type_map(self) -> Dict[type, type]:
		return {
			SBatch: SBatch,
			VBatch: VBatch,
			LVBatch: LVBatch,
			VMultiBatch: VMultiBatch,
			LVMultiBatch: LVMultiBatch,
		}

	def process(self, data: Batch) -> Batch:
		ty = type(data)

		if ty in [SBatch, VBatch, LVBatch]:
			data.data = np.clip(data.data, self.cfg['low'], self.cfg['high'])
			np.nan_to_num(data.data, nan=0.0, copy=False)
		elif ty in [VMultiBatch, LVMultiBatch]:
			for item in data.items.values():
				item.data = np.clip(item.data, self.cfg['low'], self.cfg['high'])
				np.nan_to_num(item.data, nan=0.0, copy=False)
		else:
			raise TypeError('Unknown type: ', ty)

		return data