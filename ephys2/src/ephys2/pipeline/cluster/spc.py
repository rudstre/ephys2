'''
SPC-based clustering stage
'''

import numpy as np
import numpy.typing as npt

from ephys2.lib.types import *
from ephys2.lib.spc import run_spc
from .base import *

class SPCStage(ClusteringStage):

    @staticmethod
    def name() -> str:
        return 'spc'

    @staticmethod
    def parameters() -> Parameters:
        return {
            'temperature': FloatParameter(
                start = 0,
                stop = np.inf,
                units = None,
                description = 'Temperature for super-paramagnetic clustering'
            ),
            'knn': IntParameter(
                start = 1,
                stop = np.inf,
                units = None,
                description = 'Maximum number of nearest-neighbors to use in SPC knn algorithm'
            ),
            'cycles': IntParameter(
                start = 1,
                stop = np.inf,
                units = None,
                description = 'Number of Swensen-Wang sweeps in SPC'
            ),
            'metric': CategoricalParameter(
                categories = ['euclidean', 'cityblock', 'cosine', 'correlation', 'hamming', 'chebyshev', 'mahalanobis'],
                units = None,
                description = 'Metric to use in distance calculations for SPC'
            ),
        }

    def process(self, data: npt.NDArray[np.float32]) -> Labeling:
        _, labelings = run_spc(
            data,
            self.cfg['temperature'],
            self.cfg['temperature'],
            1,
            self.cfg['cycles'],
            self.cfg['knn'],
            metric=self.cfg['metric'],
            random_seed=0
        )
        assert labelings.shape[0] == 1
        return labelings[0]

