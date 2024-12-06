'''
Store for LTBatch data
'''
import h5py

from ephys2.lib.types import *
from ephys2.lib.array import *
from ephys2.lib.h5.ltbatch import *
from ephys2.gui.types import *
from ephys2.gui.tbatch.store import *

class LTMultiBatchStore(TMultiBatchStore):

	def dispatch(self, action: GUIAction):

		if action.tag == 'set_file':
			self['filepath'] = action.payload
			with h5py.File(action.payload, 'r') as file:
				assert file.attrs['tag'] == 'LTMultiBatch'
				self.file_keys = list(file.keys())
				N_x = 0
				for key in self.file_keys:
					N_x = max(N_x, file[key]['time'].shape[0])
				self['N_x'] = N_x
				self['N_y'] = len(self.file_keys)
				self['window_y'] = min(self['window_y'], self['N_y'])
				self.reload_data()

		else:
			super().dispatch(action)

	''' Private methods '''

	def reload_data(self):
		with h5py.File(self['filepath'], 'r') as file:
			items = dict()
			item_ids = self.file_keys[self['pos_y'] : self['pos_y'] + self['window_y']]
			self['window_y'] = min(self['window_y'], len(item_ids))
			rng_lo, rng_hi = 0, np.inf
			for item_id in item_ids:
				ltime = file[item_id]['time'][self['pos_x'] : self['pos_x'] + self['window_x']]
				rng_lo = max(min_def(ltime, 0), rng_lo)
				rng_hi = min(max_def(ltime, 0), rng_hi)
				items[item_id] = LTBatch(
					time = ltime,
					labels = file[item_id]['labels'][self['pos_x'] : self['pos_x'] + self['window_x']],
					overlap = 0
				)
			self['range'] = (rng_lo, rng_hi)
			self['data'] = LTMultiBatch(items=items)
