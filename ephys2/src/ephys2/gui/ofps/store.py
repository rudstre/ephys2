'''
OFPS store
'''
import numpy as np
import pdb

from ephys2.lib.types import *
from ephys2.pipeline.input.intan_ofps import *
from ephys2.gui.sbatch.store import *

class OFPSStore(SBatchStore):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.ofps_loader = None

	def dispatch(self, action: GUIAction):

		if action.tag == 'set_file':
			with self.atomic():
				self['filepath'] = action.payload
				self.ofps_loader = IntanOfpsStage({
					'start': 0,
					'stop': np.inf,
					'batch_size': np.inf,
					'batch_overlap': 0,
					'sessions': [[RangedDirectory(
						path = action.payload
					)]],
					'datetime_pattern': '*',
				})
				self.ofps_loader.initialize()
				self['N_x'] = self.ofps_loader.all_metadata[0].size
				self['N_y'] = self.ofps_loader.all_metadata[0].n_channels
				self.reload_data()

		else:
			super().dispatch(action)

	def reload_data(self):
		data = self.ofps_loader.load(
			self['pos_x'],
			self['pos_x'] + self['window_x'] * 2
		)
		if not (self.bp_filter is None):
			data = self.bp_filter.process(data)
		self['data'] = data


