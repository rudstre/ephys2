import numpy as np
from typing import Dict

from ephys2.lib.sparse import *
from ephys2.lib.types import *

'''
Class-tag association
'''
class_tag_map: Dict[str, type] = {
	'Array': np.ndarray,
	'CSR': CSRMatrix,
	'SBatch': SBatch,
	'TBatch': TBatch,
	'VBatch': VBatch,
	'LVBatch': LVBatch,
	'SLVBatch': SLVBatch,
	'LLVBatch': LLVBatch,
	'SLLVBatch': SLLVBatch,
	'VMultiBatch': VMultiBatch,
	'LVMultiBatch': LVMultiBatch,
	'LLVMultiBatch': LLVMultiBatch,
	'SLLVMultiBatch': SLLVMultiBatch,
}
