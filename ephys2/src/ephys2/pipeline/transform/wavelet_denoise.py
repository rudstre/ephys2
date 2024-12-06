'''
Denoise using truncated discrete wavelet transform
'''
import numpy as np
import numpy.typing as npt
import pywt

from ephys2.lib.types import *
from ephys2.lib.transforms import truncated_dwt

class WaveletDenoiseStage(ProcessingStage):

    @staticmethod
    def name() -> str:
        return 'wavelet_denoise'

    def type_map(self) -> Dict[type, type]:
        return {npt.NDArray[np.float32]: npt.NDArray[np.float32]}

    @staticmethod
    def parameters() -> Parameters:
        return {
            'wavelet': CategoricalParameter(
				categories = pywt.wavelist(kind='discrete'),
				units = None,
				description = 'Choice of wavelet used in discrete wavelet transform feature extraction; set to none or one of http://wavelets.pybytes.com/'
			),
        }

    def process(self, data: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return truncated_dwt(data, self.cfg['wavelet'])