'''
SLVBatch store
'''
import numpy as np
import h5py

from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.h5.slvbatch import *
from ephys2.lib.h5.utils import *
from ephys2.gui.llvbatch.store import *

'''
Store
'''

class SLLVMultiBatchStore(LLVMultiBatchStore):
	default_window: int = 10000000 # Increase default window size for summarized data

	def __init__(self):
		super().__init__()
		self.detail_store = LLVMultiBatchStore() # Sub-store holding state for detail view

	def initial_state(self) -> GUIState:
		return super().initial_state() | {
			'view_mode': 'summary',
		}

	def make_loader(self, **kwargs) -> BatchLoader:
		return SLLVBatchLoader(**kwargs)

	@property
	def split_serializer(self) -> type:
		return H5SLLVBatchSerializer

	def dispatch(self, action: GUIAction):
		if action.tag == 'jump_to_detail':
			with self.atomic():
				x1, x2 = action.payload, action.payload + global_metadata['sampling_rate'] * 600 # Keep 10 minutes of data visible
				self.detail_store.dispatch(GUIAction(tag='set_window', payload=(x1, x2)))
				self['view_mode'] = 'detail'
				
		else:
			super().dispatch(action)

			
'''
Loader
'''

@dataclass
class SLLVBatchLoader(LLVBatchLoader):

	@property
	def serializer(self) -> type:
		return H5SLVBatchSerializer_GUI # This loader only loads summarized data

	def get_sample_indices(self, sample: int) -> Tuple[int, int]:
		assert len(self.filepaths) == 1, 'Cannot currently search across multiple files'
		with h5py.File(self.filepaths[0], 'r') as file:
			return binary_search_interval(file[self.item_id]['summary']['time'], sample)
