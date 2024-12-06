'''
Store for LVBatch data
'''
from multiprocessing import context
import numpy as np
from contextlib import contextmanager
import traceback
import h5py

from ephys2.lib.array import combine_masks
from ephys2.lib.types import *
from ephys2.lib.h5.lvbatch import *
from ephys2.lib.h5.utils import *
from ephys2.gui.multibatch.store import *
from ephys2.gui.vbatch.store import *
from ephys2 import _cpp

'''
Store
'''

class LVMultiBatchStore(MultiBatchStore):

	def make_loader(self, **kwargs) -> BatchLoader:
		return LVBatchLoader(**kwargs)

	def initial_state(self) -> GUIState: 
		return MultiBatchStore.initial_state(self) | {
			'selected_units': set(),
			'hidden_units': None,
			'excluded_units': None,
			'exported_units': None,
			'excluded_or_exported_units': None, # Cached for performance
			'isolated_units': None, # Units which are isolated; takes precedence over the other view filters
			'showing_visible': True,
			'showing_hidden': True,
			'showing_excluded': True,
			'showing_exported': True,
			'showing_workspace': True,
		}

	def compute_mask(self) -> Mask:
		# Remove units satisfying any of the below conditions
		filter_sets = []
		if self['isolated_units'] is None:
			if not self['showing_visible']:
				filter_sets.append((self['hidden_units'], False))
			if not self['showing_hidden']:
				filter_sets.append((self['hidden_units'], True))
			if not self['showing_excluded']:
				filter_sets.append((self['excluded_units'], True))
			if not self['showing_exported']:
				filter_sets.append((self['exported_units'], True))
			if not self['showing_workspace']:
				filter_sets.append((self['excluded_or_exported_units'], False))
		else:
			filter_sets.append((self['isolated_units'], False))
		mask = slice(None)
		if len(filter_sets) > 0:
			labels = self['data'].labels
			mask = np.full(labels.size, True, dtype=bool)
			_cpp.apply_venn_mask(filter_sets, labels, mask)
		return mask

	def dispatch(self, action: GUIAction):

		if action.tag == 'select':
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					selected = self['selected_units']
					if is_shift_pressed():
						if action.payload in selected:
							selected.discard(action.payload)
						else:
							selected.add(action.payload)
					else:
						selected = {action.payload}
					self['selected_units'] = selected

		elif action.tag == 'reset_view' and self.has_data():
			with self.atomic():
				self['isolated_units'] = self.current_loader.isolated_units = None
				MultiBatchStore.dispatch(self, action)

		elif action.tag in ['up', 'down', 'set_chgroup']:
			with profiling(on=global_settings.gui_profiling_on):
				with self.atomic():
					self['selected_units'] = set() # Reset selection when changing channel group
					MultiBatchStore.dispatch(self, action)

		elif action.tag == 'set_showing_status':
			with self.atomic():
				status, checked = action.payload
				if status == 'visible':
					self['showing_visible'] = checked
				elif status == 'hidden':
					self['showing_hidden'] = checked
				elif status == 'excluded':
					self['showing_excluded'] = checked
				elif status == 'exported':
					self['showing_exported'] = checked
				elif status == 'workspace':
					self['showing_workspace'] = checked
				else:
					raise ValueError(f'Unknown status {status}')
				self.recompute_visible()

		elif action.tag == 'set_selected_status':
			with self.atomic():
				status = action.payload
				if status == 'visible':
					self['hidden_units'] =  self.current_loader.hidden_units = self['hidden_units'] - self['selected_units']
					self['showing_visible'] = True
				elif status == 'hidden':
					self['hidden_units'] =  self.current_loader.hidden_units = self['hidden_units'] | self['selected_units']
					self['showing_hidden'] = False
				elif status == 'excluded':
					self['excluded_units'] = self.current_loader.excluded_units = self['excluded_units'] | self['selected_units']
					self['exported_units'] = self.current_loader.exported_units = self['exported_units'] - self['selected_units']
					self['edited'] = True
				elif status == 'exported':
					self['exported_units'] = self.current_loader.exported_units = self['exported_units'] | self['selected_units']
					self['excluded_units'] = self.current_loader.excluded_units = self['excluded_units'] - self['selected_units']
					self['edited'] = True
				elif status == 'workspace':
					self['excluded_units'] = self.current_loader.excluded_units = self['excluded_units'] - self['selected_units']
					self['exported_units'] = self.current_loader.exported_units = self['exported_units'] - self['selected_units']
					self['edited'] = True
				elif status == 'isolated':
					self['isolated_units'] = self.current_loader.isolated_units = self['selected_units']
				else:
					raise ValueError(f'Unknown status {status}')
				self.recompute_visible()

		elif action.tag == 'set_unit_status':
			with self.atomic():
				unit, status = action.payload
				if status == 'workspace':
					self['excluded_units'].discard(unit)
					self['exported_units'].discard(unit)
				elif status == 'excluded':
					self['excluded_units'].add(unit)
					self['exported_units'].discard(unit)
				elif status == 'exported':
					self['excluded_units'].discard(unit)
					self['exported_units'].add(unit)
				else:
					raise ValueError(f'Unknown status {status}')
				# Trigger listeners
				self['excluded_units'] = self.current_loader.excluded_units = self['excluded_units'] 
				self['exported_units'] = self.current_loader.exported_units = self['exported_units']
				self['edited'] = True
				self.recompute_visible()

		elif action.tag == 'set_unit_visibility':
			with self.atomic():
				unit, visible = action.payload
				if visible:
					self['hidden_units'].discard(unit)
				else:
					self['hidden_units'].add(unit)
				# Trigger listeners
				self['hidden_units'] = self.current_loader.hidden_units = self['hidden_units'] 
				self.recompute_visible()

		else:
			MultiBatchStore.dispatch(self, action)

	def post_load_data(self):
		# Update store fields for listeners
		self['excluded_units'] = self.current_loader.excluded_units
		self['hidden_units'] = self.current_loader.hidden_units
		self['exported_units'] = self.current_loader.exported_units
		self['isolated_units'] = self.current_loader.isolated_units
		self['excluded_or_exported_units'] = self['excluded_units'] | self['exported_units']

'''
Loader
'''

@dataclass
class LVBatchLoader(VBatchLoader):

	def __post_init__(self):
		assert len(self.filepaths) == 1, 'Cannot load labeled data from multiple files currently.'
		with h5py.File(self.filepaths[0], 'r') as file:
			item_dir = file[self.item_id]
			self.excluded_units = set(item_dir['excluded_units'][:]) if 'excluded_units' in item_dir else set() # Load excluded units
			self.exported_units = set(item_dir['exported_units'][:]) if 'exported_units' in item_dir else set() # Load exported units
			self.hidden_units = set()
			self.isolated_units = None
		super().__post_init__()

	@property
	def serializer(self) -> type:
		return H5LVBatchSerializer 

	def render(self, data: LVBatch) -> LVBatch:
		return data

	def save_edits(self):
		with h5py.File(self.filepaths[0], 'a') as file:
			item_dir = file[self.item_id]
			if 'excluded_units' in item_dir:
				del item_dir['excluded_units']
			item_dir.create_dataset('excluded_units', data=np.array(list(self.excluded_units), dtype=np.int64))
			if 'exported_units' in item_dir:
				del item_dir['exported_units']
			item_dir.create_dataset('exported_units', data=np.array(list(self.exported_units), dtype=np.int64))
