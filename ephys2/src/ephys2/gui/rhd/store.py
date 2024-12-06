'''
RHD store
'''
import numpy as np

from ephys2.lib.types import *
from ephys2.pipeline.input.rhd2000 import *
from ephys2.gui.sbatch.store import *

class RHDStore(SBatchStore):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.rhd_loader = None

	def dispatch(self, action: GUIAction):

		if action.tag == 'set_file':
			with self.atomic():
				self['filepath'] = action.payload
				self.rhd_loader = RHD2000Stage({
					'start': 0,
					'stop': np.inf,
					'batch_size': np.inf,
					'batch_overlap': 0,
					'sessions': [[RORangedFilePath(
						path = action.payload
					)]],
					'datetime_pattern': '*',
				})
				self.rhd_loader.initialize()
				self['N_x'] = self.rhd_loader.all_metadata[0].size
				self['N_y'] = self.rhd_loader.all_metadata[0].n_channels
				self.reload_data()

		else:
			super().dispatch(action)

	def reload_data(self):
		data = self.rhd_loader.load(
			self['pos_x'],
			self['pos_x'] + self['window_x'] * 2
		)
		if not (self.bp_filter is None):
			data = self.bp_filter.process(data)
		self['data'] = data


