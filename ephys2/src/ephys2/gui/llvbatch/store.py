'''
Store for LLVBatch data
'''
import numpy as np
from timeit import default_timer 
import traceback
from dataclasses import dataclass

from ephys2.lib.array import combine_masks
from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.h5.llvbatch import *
from ephys2.lib.h5.lvbatch import *
from ephys2.gui.multibatch.store import *
from ephys2.gui.lvbatch.store import *
from ephys2.gui.utils import show_error

'''
Store
'''

class LLVMultiBatchStore(LVMultiBatchStore):

	def make_loader(self, **kwargs) -> BatchLoader:
		return LLVBatchLoader(**kwargs)

	def initial_state(self) -> GUIState: 
		return LVMultiBatchStore.initial_state(self) | {
			'split_mode': False, 
		}

	@property
	def split_serializer(self) -> type:
		return H5LLVBatchSerializer

	def dispatch(self, action: GUIAction):

		if action.tag == 'merge_selected':
			with self.atomic():
				if len(self['selected_units']) >= 2:
					item_id = str(self['item_id'])
					self.current_loader.linkage = add_links(self.current_loader.linkage, list(self['selected_units']))
					self.current_loader.rerender() # Re-link the labels following a merge
					# Update sets
					new_label = min(self['selected_units']) # The single merged cluster
					other_labels = set(self['selected_units']) - {new_label}
					self['hidden_units'] = self.current_loader.hidden_units = self['hidden_units'] - other_labels
					self['excluded_units'] = self.current_loader.excluded_units = self['excluded_units'] - other_labels
					self['exported_units'] = self.current_loader.exported_units = self['exported_units'] - other_labels
					self['selected_units'] = {new_label} 
					self['edited'] = True
					self.recompute_visible()

		elif action.tag == 'start_split':
			with self.atomic():
				self['split_mode'] = True

		elif action.tag == 'reset_view':
			with self.atomic():
				self['split_mode'] = False
				LVMultiBatchStore.dispatch(self, action)

		elif action.tag in ['split_1d', 'split_2d']:
			with self.atomic():
				assert self['split_mode']
				t0 = default_timer()
				assert len(self['filepaths']) == 1, 'Cannot save edits across multiple files currently'
				item_id = str(self['item_id'])
				split_label = action.payload['label']
				print(f'Performing split operation on label {split_label}...')
				with h5py.File(self['filepaths'][0], 'a') as file:
					item_dir = file[item_id]
					if action.tag == 'split_1d':
						# Perform 1D split
						linkage, label_map = self.split_serializer.split_1d(
							item_dir, 
							split_label, 
							self.visible_to_real_indices(action.payload['start_index']),
							linkage = self.current_loader.linkage
						)
					else:
						# Perform 2D split
						linkage, label_map = self.split_serializer.split_2d(
							item_dir, 
							split_label, 
							self.visible_to_real_indices(action.payload['indices']),
							linkage = self.current_loader.linkage
						)
					# H5LLVBatchSerializer.check(item_dir, full=True) # Uncomment to perform consistency check
				print(f'Finished in {default_timer() - t0} seconds.')	
				self.current_loader.linkage = linkage
				self['split_mode'] = False
				new_units = set(np.unique(link_labels(np.array(list(label_map.values()), dtype=np.int64), linkage))) # Compute new units for isolation & selection
				self['selected_units'] = self['selected_units'] | new_units
				if self['isolated_units'] != None:
					self['isolated_units'] = self.current_loader.isolated_units = self['isolated_units'] | new_units
				if split_label in self['excluded_units']:
					self['excluded_units'] = self.current_loader.excluded_units = self['excluded_units'] | new_units
				elif split_label in self['exported_units']:
					self['exported_units'] = self.current_loader.exported_units = self['exported_units'] | new_units
				if split_label in self['hidden_units']:
					self['hidden_units'] = self.current_loader.hidden_units = self['hidden_units'] | new_units
				self['edited'] = True
				self.recompute_visible(force_reload=True) # Reload data & re-link labels following a split

		elif action.tag in ['up', 'down', 'right', 'left', 'zoom_in', 'zoom_out']:
			# Disable keyboard navigation when in split mode
			if not self['split_mode']:
				LVMultiBatchStore.dispatch(self, action)

		else:
			LVMultiBatchStore.dispatch(self, action)


'''
Loader
'''

@dataclass
class LLVBatchLoader(LVBatchLoader):

	def __post_init__(self):
		assert len(self.filepaths) == 1, 'Cannot load linked data from multiple files currently.'
		with h5py.File(self.filepaths[0], 'r') as file:
			self.linkage = H5CSRSerializer.load(file[self.item_id]['linkage']) # Load links matrix
		super().__post_init__()

	@property
	def serializer(self) -> type:
		return H5LVBatchSerializer # Since we load the full links matrix from the beginning, use the LVBatch loader to avoid spending time loading sparse matrices

	def render(self, data: LVBatch) -> LVBatch:
		data.labels = link_labels(data.labels, self.linkage)
		return data

	def save_edits(self):
		super().save_edits()
		with h5py.File(self.filepaths[0], 'a') as file:
			H5CSRSerializer.replace(file[self.item_id]['linkage'], self.linkage)