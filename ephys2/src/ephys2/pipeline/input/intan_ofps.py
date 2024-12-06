'''
Read Intan "One file per signal type" into contiguous in-memory NumPy arrays.

Python wrapper uses `intanutil` library to read header (metadata), with C++ extension for reading amplifier signals.

Datasheet:
https://intantech.com/files/Intan_RHD2000_data_file_formats.pdf
'''

from typing import Tuple, Dict, Any, Optional
import numpy as np
import pdb
import os
import time

import ephys2.lib.intanutil.header as iheader
import ephys2._cpp as _cpp
from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, logger
from ephys2.lib.array import *
from .base import *
from .intan.auxilliary import *

@dataclass
class OfpsMetadata(DirInputMetadata):
	sample_rate: int
	n_channels: int
	time_path: ROFilePath
	amp_path: ROFilePath
	aio_path: ROFilePath
	dio_path: ROFilePath
	header: dict

''' One file per signal type '''
	
class IntanOfpsStage(ParallelDirectoriesInputStage):

	@staticmethod
	def name() -> str:
		return 'intan_ofps'

	def output_type(self) -> type:
		return SBatch

	@staticmethod
	def parameters() -> Parameters:
		return ParallelDirectoriesInputStage.parameters() | RHDAuxStage.parameters() 

	def initialize(self):
		RHDAuxStage.initialize(self)

	def make_input_metadata(self, rd: RangedDirectory, session: int) -> DirInputMetadata:
		with open(f'{rd.path}/info.rhd', 'rb') as f:
			header = iheader.read_header(f)

		time_path = f'{rd.path}/time.dat'
		filesize = os.path.getsize(time_path)
		num_samples = filesize // 4 # Time is a 32-bit integer

		# Validate aux channels
		RHDAuxStage.validate_aux_metadata(self, header)
		self.n_total_aio = len(header['aux_input_channels'])

		# Record sampling rate
		global_metadata['sampling_rate'] = header['sample_rate']
		
		return OfpsMetadata(
			size = num_samples,
			start = rd.start,
			stop = rd.stop,
			offset = 0,
			path = rd.path,
			session = session,
			sample_rate = header['sample_rate'],
			n_channels = header['num_amplifier_channels'],
			time_path = time_path,
			amp_path = f'{rd.path}/amplifier.dat',
			aio_path = f'{rd.path}/auxiliary.dat',
			dio_path = f'{rd.path}/digitalin.dat',
			header = header
		)

	def load(self, start: int, stop: int) -> SBatch:
		RHDAuxStage.initialize_aux_batches(self)
		data = super().load(start, stop)
		RHDAuxStage.write_aux_batches(self)
		return data

	def load_from(self, md: OfpsMetadata, start: int, stop: int, time: npt.NDArray[np.int64]) -> SBatch:
		# Request data with a start offset in order to query digital change times
		start_offset = 1 if start > 0 else 0
		start -= start_offset
		N = stop - start

		# We ignore the time recorded in the actual files, since they may roll over
		# amp_t = np.fromfile(md.time_path, dtype=np.int32, count=N, offset=start*4).astype(np.int64)
		amp_data = 0.195 * np.fromfile(md.amp_path, dtype=np.int16, count=N*md.n_channels, offset=start*md.n_channels*2).astype(np.float32)
		amp_data.shape = (N, md.n_channels)

		# Capture aux data
		if self.digital_in:
			dio_data = read_binary_array(md.dio_path, np.uint16(), (N,), start)
			assert dio_data.shape == (time.shape[0] + start_offset,)
			RHDAuxStage.capture_dio(self, md, dio_data, time, start_offset)
		if self.analog_in:
			aio_data = 0.0000374 * read_binary_array(md.aio_path, np.uint16(), (N, self.n_total_aio), start).astype(np.float32)
			assert aio_data.shape[0] == (time.shape[0] + start_offset)
			RHDAuxStage.capture_aio(self, md, aio_data, time, start_offset, md.sample_rate)

		return SBatch(
			time = time,
			data = amp_data[start_offset:],
			overlap = 0,
			fs = md.sample_rate
		)

	def finalize(self):
		RHDAuxStage.finalize(self)

	def cleanup(self):
		RHDAuxStage.cleanup(self)

