'''
Store for VBatch data
'''
import h5py

from ephys2.lib.types import *
from ephys2.lib.h5.sbatch import *
from ephys2.gui.types import *
from ephys2.pipeline.preprocess.iirfilter import *
from ephys2.lib.singletons import global_metadata

class SBatchStore(GUIStore):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.bp_filter = None

	def initial_state(self) -> GUIState:
		return {
			'filepath': None,
			'data': None,
			'time': None,
			'window_x': 10000,
			'window_y': 32, # Default show tetrode
			'pos_x': 0,
			'pos_y': 0,
			'N_x': None,
			'N_y': None,
			'speed': 400,
			'signal_height': 100,
			'highpass': 0,
			'lowpass': np.inf,
			'median': False,
			'color_group': 4, # Default tetrode coloring
			'threshold': np.inf, 
		}

	def dispatch(self, action: GUIAction):

		if action.tag == 'set_file':
			self['filepath'] = action.payload
			with h5py.File(action.payload, 'r') as file:
				assert file.attrs['tag'] == 'SBatch'
				self['N_x'] = file['data'].shape[0]
				self['N_y'] = file['data'].shape[1]
				self['window_y'] = min(self['window_y'], self['N_y'])
				self.reload_data()

				# Read metadata
				if 'metadata' in file.attrs:
					global_metadata.read_from_string(file.attrs['metadata'])

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

		elif action.tag == 'set_highpass':
			with self.atomic():
				self['highpass'] = action.payload
				self._redesign_filter()
				self.reload_data()

		elif action.tag == 'set_lowpass':
			with self.atomic():
				self['lowpass'] = action.payload
				self._redesign_filter()
				self.reload_data()

		elif action.tag == 'skip_to':
			if action.payload < np.inf:
				self['pos_x'] = min(self['N_x'] - self['window_x'], action.payload)
			else:
				self['pos_x'] = max(0, self['N_x'] - self['window_x'])
			self.reload_data()

		elif action.tag == 'set_window':
			with self.atomic():
				dW = self['window_x'] - action.payload
				start = max(0, self['pos_x'] + dW // 2)
				stop = min(self['N_x'], start + action.payload)
				self['pos_x'] = start
				self['window_x'] = stop - start
				self.reload_data()

		elif action.tag == 'set_color_group':
			self['color_group'] = action.payload

		elif action.tag == 'set_threshold':
			self['threshold'] = action.payload

		elif action.tag == 'set_signal_height':
			self['signal_height'] = action.payload

		else:
			raise ValueError(f'Received unknown action: {action}')

	''' Private methods '''

	def _redesign_filter(self):
		self.bp_filter = BandpassStage({
			'order': 2,
			'highpass': self['highpass'],
			'lowpass': self['lowpass'],
			'Rp': 0.2, # Maximum ripple in the passband (dB)
	    'Rs': 100, # Minimum attenuation in the stopband (dB)
	    'type': 'ellip', # Filter type (options: `ellip`, `cheby1`, `cheby2`), see https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.iirdesign.html
	    'padding_type': 'odd', # Signal extension method (others supported: `odd`, `even`)
	    'padding_length': 1000, # Edge padding
		})
		self.bp_filter.initialize()

	def reload_data(self):
		with h5py.File(self['filepath'], 'r') as file:
			stime = file['time'][
				self['pos_x'] : self['pos_x'] + self['window_x'] * 2
			]
			sdata = file['data'][
				self['pos_x'] : self['pos_x'] + self['window_x'] * 2
			]
			self['window_y'] = min(self['window_y'], sdata.shape[1])
			fs = int(file.attrs['fs'])
			data = SBatch(
				time = stime, data = sdata, fs = fs, overlap = 0
			)
			if not (self.bp_filter is None):
				data = self.bp_filter.process(data)
			self['data'] = data
