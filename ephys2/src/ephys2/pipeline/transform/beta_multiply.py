'''
Elementwise weighting by Beta distribution
'''
import numpy as np
import numpy.typing as npt

from ephys2.lib.types import *
from ephys2.lib.transforms import beta_weighted

class BetaMultiplyStage(ProcessingStage):

    @staticmethod
    def name() -> str:
        return 'beta_multiply'

    def type_map(self) -> Dict[type, type]:
        return {npt.NDArray[np.float32]: npt.NDArray[np.float32]}

    @staticmethod
    def parameters() -> Parameters:
        return {
            'beta': FloatParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Parameter of symmetric Beta distribution used to weight spike waveforms prior to clustering'
			),
        }

    def process(self, data: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        return beta_weighted(data, self.cfg['beta'])