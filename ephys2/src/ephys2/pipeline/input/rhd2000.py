'''
Fast and parallel routines for reading RHD amplifier data into contiguous in-memory NumPy arrays.

Python wrapper uses `intanutil` library to read header (metadata), with C++ extension for reading amplifier signals.

Datasheet:
https://intantech.com/files/Intan_RHD2000_data_file_formats.pdf
'''

from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
import pdb
import os
import time

import ephys2.lib.intanutil.header as iheader
import ephys2._cpp as _cpp
from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, logger, global_state
from ephys2.lib.h5 import *

from .base import *
from .intan.auxilliary import *
	
@dataclass
class RHD2000Metadata(FileInputMetadata):
	sample_rate: int
	n_channels: int
	header_offset: int
	bytes_per_block: int
	bytes_after_amp: int
	samples_per_block: int
	num_blocks: int
	n_analog_channels: int
	digital_in_enabled: bool
	header: dict

	@property
	def num_samples(self) -> int:
		return self.samples_per_block * self.num_blocks

class RHD2000Stage(ParallelFilesInputStage):

	@staticmethod
	def name() -> str:
		return 'rhd2000'

	def output_type(self) -> type:
		return SBatch

	@staticmethod
	def parameters() -> Parameters:
		return ParallelFilesInputStage.parameters() | RHDAuxStage.parameters() 

	def initialize(self):
		RHDAuxStage.initialize(self)

	def make_input_metadata(self, f: RORangedFilePath, session: int) -> FileInputMetadata:
		filesize = os.path.getsize(f.path)
		with open(f.path, 'rb') as file:
			header = iheader.read_header(file)
			header_offset = file.tell()
		bytes_per_block = iheader.get_bytes_per_data_block(header)
		samples_per_block = header['num_samples_per_data_block']
		num_blocks = int((filesize - header_offset) / bytes_per_block)
		size = samples_per_block * num_blocks

		# Validate aux channels
		RHDAuxStage.validate_aux_metadata(self, header)

		assert header['num_board_dig_out_channels'] == 0, 'Board has a nonzero number of digital out channels, which changes the offset.'

		# Record sampling rate
		global_metadata['sampling_rate'] = header['sample_rate']

		return RHD2000Metadata(
			path = f.path, 
			session = session,
			size = size,
			start = f.start,
			stop = f.stop,
			offset = 0,
			sample_rate = header['sample_rate'],
			n_channels = header['num_amplifier_channels'],
			header_offset = header_offset,
			bytes_per_block = bytes_per_block,
			bytes_after_amp = iheader.get_bytes_after_amp(header),
			samples_per_block = header['num_samples_per_data_block'],
			num_blocks = num_blocks,
			n_analog_channels = header['num_aux_input_channels'] if self.analog_in else 0,
			digital_in_enabled = self.digital_in and (header['num_board_dig_in_channels'] > 0), # As noted in RHD2000 datasheet, if any digital inputs are enabled, all are recorded as a 16-bit word
			header = header
		)

	def load(self, start: int, stop: int) -> SBatch:
		RHDAuxStage.initialize_aux_batches(self)
		data = super().load(start, stop)
		RHDAuxStage.write_aux_batches(self)
		return data

	def load_from(self, md: RHD2000Metadata, start: int, stop: int, time: npt.NDArray[np.int64]) -> SBatch:
		# Request data with a start offset in order to query digital change times
		start_offset = 1 if start > 0 else 0

		# We ignore the time recorded in the actual files, since they may roll over
		_, amp_data, analog_data, digital_data = _cpp.read_rhd2000_batch(
			md.path, 
			md.header_offset, 
			md.bytes_per_block, 
			md.bytes_after_amp,
			md.samples_per_block, 
			start - start_offset, 
			stop, 
			md.n_channels,
			md.n_analog_channels,
			md.digital_in_enabled
		)
		assert amp_data.shape[0] == digital_data.shape[0] == analog_data.shape[0] == (time.shape[0] + start_offset)

		# Capture aux data
		if self.digital_in:
			RHDAuxStage.capture_dio(self, md, digital_data, time, start_offset)
		if self.analog_in:
			RHDAuxStage.capture_aio(self, md, analog_data, time, start_offset, md.sample_rate)

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
	