'''
HDF5 serializer for signal batch.
'''

from typing import Optional
import pdb

from .base import *
from .vbatch import *

from ephys2.lib.types.sbatch import *

class H5SBatchSerializer(H5Serializer):

	@classmethod
	def data_type(cls: type) -> type:
		return SBatch

	@classmethod
	def version(cls: type) -> int:
		return 0

	@classmethod
	def attrs(cls: type) -> List[str]:
		return ['fs']

	@classmethod
	def parent(cls: type) -> type:
		return H5VBatchSerializer

	def init_chunks(self, h5dir: H5Dir, data: SBatch):
		h5dir.attrs['fs'] = data.fs
		self.fs = data.fs

	def init_serialize(self, out_dir: H5Dir):
		out_dir.attrs['fs'] = self.fs

	@classmethod
	def check(cls: type, h5dir: H5Dir, full=False):
		H5VBatchSerializer.check(h5dir, full)
		assert h5dir.attrs['fs'] == int(h5dir.attrs['fs']) > 0

	@classmethod
	def get_size(cls: type, h5dir: H5Dir) -> int:
		return h5dir['time'].shape[0]

	@classmethod
	def load(cls: type, h5dir: H5Dir, start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0) -> SBatch:
		return SBatch.from_vb(
			H5VBatchSerializer.load(h5dir, start, stop, overlap),
			fs=int(h5dir.attrs['fs'])
		)

	@classmethod
	def load_sparse(cls: type, h5dir: H5Dir, indices: npt.NDArray[np.int64]) -> SBatch:
		return SBatch.from_vb(
			H5VBatchSerializer.load_sparse(h5dir, indices),
			fs=int(h5dir.attrs['fs'])
		)

	@classmethod
	def load_multi(cls: type, h5dirs: List[H5Dir], start: Optional[int]=None, stop: Optional[int]=None, overlap: int=0, time_offsets: Optional[List[int]]=None) -> SBatch:
		return SBatch.from_vb(
			H5VBatchSerializer.load_multi(h5dirs, start, stop, overlap, time_offsets),
			fs=int(h5dirs[0].attrs['fs'])
		)
