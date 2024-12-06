'''
Common types
'''

import numpy as np
from dataclasses import dataclass
from typing import Generator, TypeVar, NewType, Dict, Union, List

# We use int64 for IDs, rather than uint64, due to NumPy's completely strange casting semantics
# https://github.com/numpy/numpy/issues/7126
ID_DTYPE = np.int64 

T = TypeVar('T')
Gen = Generator[T, None, None]

FilePath = NewType('FilePath', str) # A FilePath without any checks 
ROFilePath = NewType('ROFilePath', str)
RWFilePath = NewType('RWFilePath', str)
Directory = NewType('Directory', str)

@dataclass
class RORangedFilePath:
	path: ROFilePath
	start: int = 0
	stop: int = np.inf

@dataclass
class RangedDirectory:
	path: Directory
	start: int = 0
	stop: int = np.inf

JSON = Dict[Union[int, str], Union[int, str, 'JSON', List['JSON']]]