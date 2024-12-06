'''
Routines for reading FAST-style 64-channel RHD amplifier data into contiguous in-memory NumPy arrays.
See https://github.com/Olveczky-Lab/FAST/blob/master/RHDFormat.txt for the data format details.
'''

from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
import pdb
import os
import time
import warnings

import ephys2._cpp as _cpp
from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, logger
from ephys2.lib.h5 import *

from .base import *
from .intan.auxilliary import *

RHD64_DIG_IN = 16
RHD64_ACC_IN = 3

class RHD64Stage(ParallelFilesInputStage):

	@staticmethod
	def name() -> str:
		return 'rhd64'

	def output_type(self) -> type:
		return SBatch

	@staticmethod
	def parameters() -> Parameters:
		return ParallelFilesInputStage.parameters() | {
			'sampling_rate': IntParameter(
				start = 1,
				stop = np.inf,
				units = 'Hz',
				description = 'Sampling rate of the original recording'
			)
		} | RHDAuxStage.parameters(aio_chs = [1, 2, 3]) # Only acc channels are available 

	def initialize(self):
		RHDAuxStage.initialize(self)

	def make_input_metadata(self, f: RORangedFilePath, session: int) -> FileInputMetadata:
		filesize = os.path.getsize(f.path)
		size = filesize // 176 # Each frame is 176 bytes; if there is not a whole number of frames, only read as far as possible.
		if filesize % 176 != 0:
			logger.warn(f'RHD64 file {f.path} did not contain a whole number of 176-byte frames; only reading until sample {size}.')

		# Validate aux channels
		RHDAuxStage.validate_aux_metadata(self)

		# Record sampling rate
		global_metadata['sampling_rate'] = self.cfg['sampling_rate']

		return FileInputMetadata(
			size = size,
			start = f.start,
			stop = f.stop,
			offset = 0,
			path = f.path,
			session = session
		)

	def load(self, start: int, stop: int) -> SBatch:
		RHDAuxStage.initialize_aux_batches(self)
		data = super().load(start, stop)
		RHDAuxStage.write_aux_batches(self)
		return data

	def load_from(self, md: FileInputMetadata, start: int, stop: int, time: npt.NDArray[np.int64]) -> SBatch:
		# Request data with a start offset in order to query digital change times
		start_offset = 1 if start > 0 else 0
		start -= start_offset
		N = stop - start
		
		# We ignore the time recorded in the actual files, since they may roll over
		_, amp_data, acc_data, digital_data = _cpp.read_rhd64_batch(
			md.path, 
			start, 
			stop, 
		)
		assert amp_data.shape[0] == digital_data.shape[0] == acc_data.shape[0] == (time.shape[0] + start_offset)
		assert acc_data.shape[1] == RHD64_ACC_IN

		# Capture aux data
		if self.digital_in:
			RHDAuxStage.capture_dio(self, md, digital_data, time, start_offset)
		if self.analog_in:
			RHDAuxStage.capture_aio(self, md, acc_data, time, start_offset, self.cfg['sampling_rate'])

		return SBatch(
			time = time,
			data = amp_data[start_offset:],
			overlap = 0,
			fs = self.cfg['sampling_rate']
		)

	def finalize(self):
		RHDAuxStage.finalize(self)

	def cleanup(self):
		RHDAuxStage.cleanup(self)
	