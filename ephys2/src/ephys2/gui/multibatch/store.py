''' 
Base abstract store for MultiBatch data 
'''
import h5py
import numpy as np
from abc import ABC, abstractmethod
import pdb
import math
from timeit import default_timer 
import warnings
import traceback

from ephys2.lib.h5 import *
from ephys2.lib.types import *
from ephys2.lib.array import *
from ephys2.lib.singletons import global_metadata, rng
from ephys2.lib.profile import profiling
from ephys2.lib.settings import global_settings

from ephys2.gui.types import *
from ephys2.gui.utils import *

'''
Store
'''

class MultiBatchStore(GUIStore, ABC):
	default_load_multiplier: int = 1 # Multiple of window to load data in (+1 on either side, set 0 for load-as-you-go behavior)
	default_window: int = 1000 # Starting window size
	default_step_percent: float = 0.1 # Step size when using navigation shortcuts
	default_zoom_percent: float = 0.1 # Zoom in or out percentage

	def initial_state(self) -> GUIState:
		return {
			'filepaths': None,
			'loaders': dict(),
			'item_id': None,
			'items': None,
			'data': None, # Subclass of VBatch, represents the slice of data accessible to widgets
			'hovered': None,
			'visible_data': None, # Subclass of VBatch, represents actual visible data
			'max_gap': np.inf, # Maximum temporal gap after which to collapse time between samples 
			'edited': False, # Whether any data has been edited
			'mask': slice(None), # Mask to apply to visible data
		}

	def dispatch(self, action: GUIAction):

		if action.tag == 'set_files':
			with self.atomic():
				filepaths = action.payload
				assert len(filepaths) > 0, 'Must receive at least one file to open'
				self['filepaths'] = filepaths
				# We assume all files have the same structure and metadata
				with h5py.File(filepaths[0], 'r') as file:
					self['items'] = ks = sorted(list(int(k) for k in file.keys()))
					if len(ks) > 0:
						self['item_id'] = ks[0]
					# Read metadata
					if 'metadata' in file.attrs:
						global_metadata.read_from_string(file.attrs['metadata'])
				self.recompute_visible()

		elif action.tag == 'reset_view' and self.has_data():
			with self.atomic():
				self.current_loader.reset()
				self.recompute_visible()

		elif action.tag == 'up' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					i = self['items'].index(self['item_id'])
					N = len(self['items'])
					i = min(N - 1, i + 1)
					self['item_id'] = self['items'][i]
					self.recompute_visible()

		elif action.tag == 'down' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					i = self['items'].index(self['item_id'])
					i = max(0, i - 1)
					self['item_id'] = self['items'][i]
					self.recompute_visible()

		elif action.tag == 'right' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					self.current_loader.step_right()
					self.recompute_visible()

		elif action.tag == 'left' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					self.current_loader.step_left()
					self.recompute_visible()

		elif action.tag == 'zoom_in' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					self.current_loader.zoom_in()
					self.recompute_visible()

		elif action.tag == 'zoom_out' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					self.current_loader.zoom_out()
					self.recompute_visible()

		elif action.tag == 'hover' and self.has_data():
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					self['hovered'] = action.payload

		elif action.tag == 'set_window' and self.has_data():
			with self.atomic():
				assert action.payload[0] < np.inf
				assert action.payload[0] <= action.payload[1]
				self.current_loader.set_window(action.payload[0], action.payload[1])
				self.recompute_visible()

		elif action.tag == 'set_chgroup' and self.has_data():
			with self.atomic():
				self['item_id'] = action.payload
				self.recompute_visible()

		elif action.tag == 'set_max_gap' and self.has_data():
			with self.atomic():
				self['max_gap'] = action.payload
				self.recompute_visible()

		elif action.tag == 'select_between' and self.has_data():
			with self.atomic():
				t1, t2 = action.payload
				assert t1 <= t2
				times = self.compute_visible_time(self['data'].time)
				idx1 = (times <= t1).argmin()
				idx2 = (times >= t2).argmax()
				self.current_loader.subselect(idx1, idx2)
				self.recompute_visible()

		elif action.tag == 'save_edits':
			with self.atomic():
				self.save_edits()

		else:
			raise Exception(f'Action of unknown type: {action.tag} received.')


	''' Overrides ''' 

	@abstractmethod
	def make_loader(sel, **kwargs) -> 'BatchLoader':
		'''
		Return the BatchLoader class for this data type
		'''
		pass

	def compute_mask(self) -> Mask:
		'''
		Compute mask to be applied to visible data
		'''
		return slice(None)

	def post_load_data(self):
		'''
		Called after data is loaded, before visible data is computed
		'''
		pass

	''' Private methods ''' 

	def visible_to_real_indices(self, visible_indices: Union[int, npt.NDArray[int]]) -> Union[int, npt.NDArray[int]]:
		'''
		Convert visible indices to real indices in the dataset
		'''
		real_indices = np.arange(self['data'].size)[self['mask']][visible_indices]
		return self.current_loader.relative_to_absolute(real_indices)

	def recompute_visible(self, force_reload=False):
		'''
		Recompute visible data from current loader
		'''
		assert self.has_data()
		# First create loader if needed
		if not self['item_id'] in self['loaders']:
			self['loaders'][self['item_id']] = self.make_loader(
				filepaths = self['filepaths'],
				item_id = str(self['item_id']),
				load_multiplier = self.default_load_multiplier,
				start = 0,
				stop = self.default_window,
				step_percent = self.default_step_percent,
				zoom_percent = self.default_zoom_percent
			)
		# Then load data
		print('Loading data...')
		t0 = default_timer()
		if force_reload:
			self.current_loader.reload()
		self['data'] = self.current_loader.load()
		print(f'Finished data load in {default_timer() - t0} seconds.')
		# Apply any post-loading step
		self.post_load_data()
		# Recompute visible data
		vis = self['data'].copy()
		vis.time = self.compute_visible_time(vis.time)
		# Apply mask
		mask = self.compute_mask()
		if type(mask) == np.ndarray:
			assert mask.shape[0] == vis.size, f'Mask shape {mask.shape[0]} does not match data shape {vis.size}'
		self['mask'] = mask
		vis = vis[mask]
		# Update state
		self['visible_data'] = vis 

	def save_edits(self):
		try:
			if self['edited']:
				t0 = default_timer()
				print(f'Saving file edits...')
				for loader in self['loaders'].values():
					loader.save_edits()
				print(f'Finished in {default_timer() - t0} seconds.')
				self['edited'] = False
		except:
			traceback.print_exc()
			show_error('Could not save the edits. Please check the terminal.')
			raise

	def has_data(self) -> bool:
		return self['items'] != None

	def compute_visible_time(self, times: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
		# Close any temporal gaps 
		min_dt = int(2 * global_metadata['sampling_rate'] / 1000)
		return collapse_time_gaps(times, self['max_gap'], min_dt)

	@property
	def current_loader(self) -> H5Serializer:
		return self['loaders'][self['item_id']]
		

'''
Batch loader with a lazily populated cache
'''

@dataclass
class BatchLoader(ABC):
	filepaths: List[str]
	item_id: str
	load_multiplier: int
	start: int
	stop: int 
	step_percent: float
	zoom_percent: float

	def __post_init__(self):
		assert 0 <= self.start <= self.stop , 'Inconsistent initial positions'
		assert 0 <= self.step_percent <= 1, 'step_percent must be in [0, 1]'
		assert 0 <= self.zoom_percent <= 1, 'zoom_percent must be in [0, 1]'

		self.time_offsets = []
		with open_h5s(self.filepaths, 'r') as files:
			self.size = sum(self.serializer.get_size(f[self.item_id]) for f in files)
			self.time_offsets = compute_time_offsets(files, global_metadata['sampling_rate'])
			for f in files:
				try:
					self.serializer.check_tag_version(f[self.item_id])
				except:
					warnings.warn('This appears to be an old ephys2 file type; there is a tag version mismatch. Some features may not work.')

		if len(self.filepaths) > 0:
			print(f'GUI loading multiple files with time offsets: {self.time_offsets}')

		self.stop = min(self.stop, self.size)
		self.reload()

	@property
	def window(self) -> int:
		return self.stop - self.start

	'''
	View modification methods (invalidates cache)
	'''

	def reset(self):
		self.start, self.stop = self.last_start, self.last_stop
		self.loaded_data_cache = None

	def step_right(self):
		if self.stop < self.size:
			wn = self.window
			dn = math.floor(wn * self.step_percent)
			self.stop = min(self.stop + dn, self.size)
			self.start = max(0, self.stop - wn)
			self.loaded_data_cache = None

	def step_left(self):
		if self.start > 0:
			wn = self.window
			dn = math.floor(wn * self.step_percent)
			self.start = max(self.start - dn, 0)
			self.stop = min(self.start + wn, self.size)
			self.loaded_data_cache = None

	def zoom_in(self):
		dn = math.floor(self.window * self.zoom_percent)
		self.start += dn
		self.stop -= dn
		self.loaded_data_cache = None

	def zoom_out(self):
		dn = math.floor(self.window * self.zoom_percent)
		self.start = max(0, self.start - dn)
		self.stop = min(self.size, self.stop + dn)
		self.loaded_data_cache = None

	def set_window(self, start_sample: int, stop_sample: int):
		# Set the window start / stop, in samples
		idx0, _ = self.get_sample_indices(start_sample)
		if stop_sample == np.inf:
			idx1 = self.size
		else:
			_, idx1 = self.get_sample_indices(stop_sample)
		self.start = max(0, idx0)
		self.stop = min(self.size, idx1)
		self.loaded_data_cache = None

	def subselect(self, idx1: int, idx2: int):
		idx1, idx2 = min(idx1, idx2), max(idx1, idx2)
		assert 0 <= idx1 <= idx2 < self.window
		self.last_start, self.last_stop = self.start, self.stop
		self.start, self.stop = self.start + idx1, self.start + idx2
		self.loaded_data_cache = None

	'''
	Load data methods
	'''

	def load(self) -> VBatch:
		if not (self.load_start <= self.start <= self.stop <= self.load_stop):
			# If the region is not loaded, do a reload
			self.reload()
		if self.loaded_data_cache is None:
			self.loaded_data_cache = self.loaded_data[(self.start - self.load_start):(self.stop - self.load_start)]
		return self.loaded_data_cache

	def reload(self):
		# Reload data from scratch with recomputed load positions
		self.load_start = max(0, self.start - self.load_multiplier * self.window)
		self.load_stop = min(self.size, self.stop + self.load_multiplier * self.window)
		self.last_start, self.last_stop = self.start, self.stop
		with open_h5s(self.filepaths, 'r') as files:
			self.loaded_data_unrendered = self.serializer.load_multi(
				[f[self.item_id] for f in files],
				start = self.load_start,
				stop = self.load_stop,
				overlap = 0,
				time_offsets = self.time_offsets
			)
		self.rerender()

	def rerender(self):
		self.loaded_data = self.render(self.loaded_data_unrendered.copy())
		self.loaded_data_cache = None # Invalidate cache 

	def relative_to_absolute(self, idx: Union[int, npt.NDArray[int]]) -> Union[int, npt.NDArray[int]]:
		# Convert relative indices to absolute indices
		return self.start + idx

	'''
	Overrides
	'''

	@property
	@abstractmethod
	def serializer(self) -> type:
		'''
		Return the H5Serializer class for this data type
		'''
		pass

	@abstractmethod
	def render(self, data: VBatch) -> VBatch:
		'''
		Perform any rendering transforms to loaded data before storing it
		'''
		pass

	def save_edits(self):
		'''
		Save any edits to the data
		'''
		pass

	@abstractmethod
	def get_sample_indices(self, sample: int) -> Tuple[int, int]:
		'''
		Return the indices of the sample in the loaded data
		'''
		pass