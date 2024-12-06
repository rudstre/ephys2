'''
Store for TBatch data
'''
import h5py

from ephys2.lib.types import *
from ephys2.lib.array import *
from ephys2.lib.h5.tbatch import *
from ephys2.gui.types import *

class TMultiBatchStore(GUIStore):

	def initial_state(self) -> GUIState:
		return {
			'filepath': None,
			'data': None,
			'time': None,
			'window_x': 100,
			'window_y': 1, 
			'pos_x': 0,
			'pos_y': 0,
			'N_x': None,
			'N_y': None,
			'range': None,
		}

	def dispatch(self, action: GUIAction):

		if action.tag == 'set_file':
			self['filepath'] = action.payload
			with h5py.File(action.payload, 'r') as file:
				assert file.attrs['tag'] == 'TMultiBatch'
				self.file_keys = list(file.keys())
				N_x = 0
				for key in self.file_keys:
					N_x = max(N_x, file[key]['time'].shape[0])
				self['N_x'] = N_x
				self['N_y'] = len(self.file_keys)
				self['window_y'] = min(self['window_y'], self['N_y'])
				self.reload_data()

		elif action.tag == 'up':
			self['pos_y'] = min(self['N_y'] - self['window_y'], self['pos_y'] + self['window_y'])
			self.reload_data()

		elif action.tag == 'down':
			self['pos_y'] = max(0, self['pos_y'] - self['window_y'])
			self.reload_data()

		elif action.tag == 'right':
			self['pos_x'] = min(self['N_x'] - self['window_x'], self['pos_x'] + self['window_x'])
			self.reload_data()

		elif action.tag == 'left':
			self['pos_x'] = max(0, self['pos_x'] - self['window_x'])
			self.reload_data()

		elif action.tag == 'zoom_in':
			dW = self['window_x'] // 10
			start = min(self['N_x'], self['pos_x'] + dW // 2)
			stop = max(0, self['pos_x'] + self['window_x'] - dW // 2)
			self['pos_x'] = start
			self['window_x'] = stop - start
			self.reload_data()

		elif action.tag == 'zoom_out':
			dW = max(2, self['window_x'] // 10)
			start = max(0, self['pos_x'] - dW // 2)
			stop = min(self['N_x'], self['pos_x'] + self['window_x'] + dW // 2)
			self['pos_x'] = start
			self['window_x'] = stop - start
			self.reload_data()

		elif action.tag == 'decrease_nchans':
			self['window_y'] = max(1, self['window_y'] - 1)
			self.reload_data()

		elif action.tag == 'increase_nchans':
			self['window_y'] = min(self['N_y'], self['window_y'] + 1)
			self.reload_data()

		else:
			raise ValueError(f'Unrecognized action: {action.tag}')

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
				items[item_id] = TBatch(
					time = ltime,
					overlap = 0
				)
			self['range'] = (rng_lo, rng_hi)
			self['data'] = TMultiBatch(items=items)
