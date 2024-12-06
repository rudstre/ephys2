'''
Base class for linking stage
'''

import numpy as np
import numpy.typing as npt

from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.graph import *

class LinkingStage(ProcessingStage):

    def type_map(self) -> Dict[type, type]:
        return {LinkCandidates: EVIncidence}