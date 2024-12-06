'''
Synthetic spikes generator from MEArec generated templates
'''
import h5py
import numpy as np
import numpy.typing as npt
import pdb

from ephys2.lib.types import *
from ephys2.pipeline.input.synthetic.base import *

class MearecSpikesStage(SyntheticSpikesStage):

	@staticmethod
	def parameters() -> Parameters:
		return SyntheticSpikesStage.parameters() | {
			'templates_file': ROFileParameter(
				units = None,
				description = 'MEARec-generated templates HDF5 containing synthetic waveforms'
			),
			'noise_std': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'μV',
				description = 'Standard deviation of added white noise'
			),
		}

	def get_num_templates(self) -> int:
		with h5py.File(self.cfg['templates_file']) as file:
			return file['templates'].shape[0]

	def get_templates(self, idxs: npt.NDArray[np.int64]) -> npt.NDArray[np.float32]:
		# H5py requires indexing in sorted order
		N = idxs.size
		idxs, inverse = np.unique(idxs, return_inverse=True) 
		with h5py.File(self.cfg['templates_file']) as file:
			data = file['templates'][idxs]
			K, M = data.shape[1], data.shape[2]
			data = data.astype(np.float32).reshape(N, K * M) # Concatenate across electrodes
			return data[inverse]

	def postprocess(self, unit_ids: npt.NDArray[np.int64], wvs: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		return wvs + np.random.normal(loc=0, scale=self.cfg['noise_std'], size=wvs.shape)
