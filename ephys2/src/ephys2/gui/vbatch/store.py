'''
Store for VBatch data
'''
import pdb
import h5py

from ephys2.lib.types import *
from ephys2.lib.h5.vbatch import *
from ephys2.lib.h5.utils import *
from ephys2.gui.multibatch.store import *

'''
Store
'''

class VMultiBatchStore(MultiBatchStore):

	def make_loader(self, **kwargs) -> BatchLoader:
		return VBatchLoader(**kwargs)


'''
Loader
'''

@dataclass
class VBatchLoader(BatchLoader):

	@property
	def serializer(self) -> type:
		return H5VBatchSerializer 

	def render(self, data: VBatch) -> VBatch:
		return data

	def get_sample_indices(self, sample: int) -> Tuple[int, int]:
		assert len(self.filepaths) == 1, 'Cannot currently search across multiple files'
		with h5py.File(self.filepaths[0], 'r') as file:
			return binary_search_interval(file[self.item_id]['time'], sample)
