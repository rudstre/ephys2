import numpy as np

from .timer import global_timer
from .metadata import global_metadata
from .state import global_state
from .logger import logger
from .profiler import profiler

rng = np.random.default_rng()