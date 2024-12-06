'''
Base class for clustering stage
'''

import numpy as np
import numpy.typing as npt

from ephys2.lib.types import *
from ephys2.lib.cluster import *

class ClusteringStage(ProcessingStage):

    def type_map(self) -> Dict[type, type]:
        return {npt.NDArray[np.float32]: Labeling}