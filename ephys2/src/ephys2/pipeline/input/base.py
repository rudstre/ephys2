'''
Base input types
'''

from abc import abstractmethod
from typing import Optional
import numpy as np
import pdb
import warnings
import datetime_glob
from datetime import timedelta
import math
import os

from ephys2.lib.mpi import MPI
from ephys2.lib.types import *
from ephys2.lib.types.config import GlobExpandingListParameter
from ephys2.lib.singletons import global_metadata, logger
from ephys2.lib.utils import *

'''
Metadata about input
'''
@dataclass
class InputMetadata:
	size: int
	start: int
	stop: int
	offset: int # Size of offset in samples (used for construction of time indices)

	def __post_init__(self):
		stop = min(self.stop, self.size)
		if stop != self.stop:
			logger.warn(f'Requested stop sample {self.stop} but only {self.size} available, stopping at {self.size}.')
			self.stop = stop
		assert self.start < self.stop, 'Start sample should be before stop sample.'

	@property
	def effective_size(self) -> int:
		return self.stop - self.start

	@property
	def end(self) -> int:
		return self.offset + self.size

	@property 
	def ignored_size(self) -> int:
		return self.start + (self.size - self.stop)

	def __str__(self):
		return 'InputMetadata(size={}, start={}, stop={}, offset={})'.format(self.size, self.start, self.stop, self.offset)

'''
Single input to be read in parallel
'''

class ParallelInputStage(InputStage):

	@staticmethod
	def parameters() -> Parameters:
		return {
			'batch_size': IntParameter(
				start = 1,
				stop = np.inf,	
				units = 'samples',
				description = 'Number of samples to read per batch; determines memory usage and batch size for subsequent stages'
			),
			'batch_overlap': IntParameter(
				start = 0,
				stop = np.inf,
				units = 'samples',
				description = 'Overlap between successively produced batches of data'
			),
		}

	def initialize(self):
		assert self.cfg['batch_overlap'] < np.inf, 'Batch overlap cannot be infinite'
		assert self.cfg['batch_overlap'] < self.cfg['batch_size'], 'Batch overlap must be at least one less than batch size in order to make progress'
		# Compute metadata about inputs
		self.metadata = self.make_metadata()
		self.current_index = self.metadata.start + ext_mul(self.rank, self.cfg['batch_size'] - self.cfg['batch_overlap'])

	def produce(self) -> Optional[Batch]:
		if self.current_index < self.metadata.stop:
			next_stop = min(self.current_index + self.cfg['batch_size'], self.metadata.stop)
			data = self.load(self.current_index, next_stop)
			self.current_index += self.n_workers * (self.cfg['batch_size'] - self.cfg['batch_overlap']) # Advance to next assigned block 
			return data

	@abstractmethod
	def make_metadata(self) -> InputMetadata:
		'''
		Make metadata about the input
		'''
		pass

	@abstractmethod
	def load(self, start: int, stop: int) -> Batch:
		'''
		Load the data in this method. Any overlap information should be correctly included 
		in the produced data, using self.cfg['batch_overlap']
		`start` and `stop` are guaranteed to respect the size field of metadata.
		'''
		pass

'''
Multiple inputs to be read in parallel
'''

class ParallelMultiInputStage(ParallelInputStage):
	'''
	Input stage for sequences of inputs (files, directories, etc.)
	Restricted to time-contiguous inputs (SBatch)
	'''

	def initialize(self):
		super().initialize()
		self.pbar = None
		self.last_metadata_i = None

	def make_metadata(self) -> InputMetadata:
		'''
		Build the metadata from the entire input
		'''
		self.all_metadata = self.make_all_metadata()
		self.n_inputs = len(self.all_metadata)

		total_size = sum(md.effective_size for md in self.all_metadata)

		return InputMetadata(
			size = total_size,
			start = 0,
			stop = total_size,
			offset = 0
		)

	@abstractmethod
	def make_all_metadata(self) -> List[InputMetadata]:
		'''
		Make metadata about each input
		'''
		pass

	def load(self, start: int, stop: int) -> VBatch:
		md_start, md_stop = start, stop
		global_size = 0
		i = 0

		while i < self.n_inputs and md_start > self.all_metadata[i].effective_size:
			md = self.all_metadata[i]
			md_start -= md.effective_size
			md_stop -= md.effective_size
			global_size += md.size + md.offset
			i += 1

		data = None
		while i < self.n_inputs and md_stop > 0:
			md = self.all_metadata[i]
			if i != self.last_metadata_i:
				logger.print(f'Loading from input: \n{md}')
				self.pbar = logger.pbar(md.effective_size, f'Progress for input {i}', 'samples')
				self.last_metadata_i = i
			input_start = max(0, md_start) + md.start
			input_stop = min(md.stop, md_stop + md.start)
			t_start = global_size + input_start + md.offset
			t_stop = global_size + input_stop + md.offset
			t_all = np.arange(t_start, t_stop, dtype=np.int64)
			chunk = self.load_from(md, input_start, input_stop, t_all)
			self.pbar.set(input_stop)
			assert chunk.overlap == 0
			if data is None:
				data = chunk
			else:
				data.append(chunk)
			md_start -= md.effective_size
			md_stop -= md.effective_size
			global_size += md.end
			i += 1

		data.overlap = max(0, self.cfg['batch_overlap'] - (self.cfg['batch_size'] - data.size)) # Effective overlap
		return data

	@abstractmethod
	def load_from(self, md: InputMetadata, start: int, stop: int, time: npt.NDArray[np.int64]) -> VBatch:
		'''
		Load data from a specific source.
		`start` and `stop` are guaranteed to respect the size field of metadata.
		'''
		pass

'''
Sequences of potentially timestamped inputs
'''

class ParallelTimestampedInputStage(ParallelMultiInputStage):
	grace_period_ms: int = np.inf # Grace period allowed for overlap between multiple files. We currently set this to inf because RHX can screw up the timestamps a lot.

	@staticmethod
	def parameters() -> Parameters:
		return ParallelMultiInputStage.parameters() | {
			'datetime_pattern': StringParameter(
				units = None,
				description = 'Datetime pattern for matching starting times from filenames; to ignore, pass "*"'
			),
		}

	def make_metadata(self) -> InputMetadata:
		'''
		Construct metadata, adding offsets accounting for timestamps as required.
		'''
		total_md = super().make_metadata()
		assert 'sampling_rate' in global_metadata, 'Metadata was not populated with the sampling rate'

		# Infer start times and offsets based on file names
		matcher = datetime_glob.Matcher(pattern=self.cfg['datetime_pattern'])
		ts = []
		names = [self.extract_name(md) for md in self.all_metadata]
		logger.print(f'Input names: {names}')
		for name in names:
			match = matcher.match(path=name)
			match = None if match is None else match.as_maybe_datetime()
			assert self.cfg['datetime_pattern'].strip() == '*' or not (match is None), f'Could not parse datetime from input {name} using the pattern {self.cfg["datetime_pattern"]}. Please specify "*" if you do not want to match a datetime or fix the pattern.'
			ts.append(match)

		# If any inputs matched the datetime, ensure all do, and that they are consistent
		if any(not (t is None) for t in ts):
			assert all(not (t is None) for t in ts), 'Some inputs parsed as a valid datetime, while others did not. Exiting.'
			logger.print(f'Inferred start times from session names: {[t.isoformat() for t in ts]}')
			logger.print(f'Inferred offsets between sessions: {[(t - ts[0]) for t in ts]}')
			last_end_time = None
			for start_time, md, name in zip(ts, self.all_metadata, names):
				if not (last_end_time is None):
					assert (self.grace_period_ms == np.inf) or (start_time >= (last_end_time - timedelta(milliseconds=self.grace_period_ms))), f'Input {name} occurred more than {self.grace_period_ms} ms before the previous end time. Expected {last_end_time.isoformat()} or later but got {start_time.isoformat()}.'
					delta = max(0, (start_time - last_end_time).total_seconds())
					# Set offset in samples from previous file
					md.offset = math.ceil(delta * global_metadata['sampling_rate'])
				last_end_time = start_time + timedelta(seconds=md.size / global_metadata['sampling_rate'])

			# Record global start time
			global_metadata['start_time'] = ts[0].isoformat()
		
		else:
			logger.print(f'No valid datetime pattern inferred from session names. Assuming all inputs are independent.')

		return total_md

	@abstractmethod
	def extract_name(self, md: InputMetadata) -> str:
		'''
		Extract the name to match the timestamp pattern against.
		'''
		pass

'''
Sequences of session inputs
'''

@dataclass
class SessionInputMetadata(InputMetadata):
	session: int # Data can be grouped into sessions

	def __str__(self):
		return f'Session {self.session}: {self.size} samples'

class ParallelSessionInputStage(ParallelTimestampedInputStage):

	@classmethod
	def parameters(cls: type) -> Parameters:
		return ParallelTimestampedInputStage.parameters() | {
			'sessions': GlobExpandingListParameter(
				element = ListParameter(element=cls.input_parameter(), units=None, description=''),
				units = None,
				description = 'Input data to read'
			),
		}

	@staticmethod
	@abstractmethod
	def input_parameter() -> Parameter:
		'''
		Type of input which can be read and grouped into sessions
		'''
		pass

	def make_metadata(self) -> InputMetadata:
		md = super().make_metadata()

		# Record the time span of data contributed by each session
		global_metadata['session_splits'] = np.cumsum([
			sum(md.end for md in mds) for mds in self.session_metadata
		]).tolist()

		# Record the lowest common ancestor of session files where per-session results can be stored
		global_metadata['session_paths'] = [
			lca_path([md.path for md in mds]) for mds in self.session_metadata
		]

		return md

	def make_all_metadata(self) -> List[SessionInputMetadata]:
		# Nested metadata structure reflects nested input structure
		self.session_metadata = [
			[self.make_input_metadata(f, session) for f in inputs]
			for session, inputs in enumerate(self.cfg['sessions'])
		]
		return flatten_list(self.session_metadata)

	@abstractmethod
	def make_input_metadata(self, f: ConfigValue, session: int) -> SessionInputMetadata:
		pass

'''
Sequences of file inputs
'''

@dataclass
class FileInputMetadata(SessionInputMetadata):
	path: ROFilePath

	def __str__(self):
		return f'File {self.path}: session {self.session}, {self.size} samples'

class ParallelFilesInputStage(ParallelSessionInputStage):

	@staticmethod
	def input_parameter() -> Parameter:
		return RORangedFileParameter(units=None, description='')

	def extract_name(self, md: FileInputMetadata) -> str:
		return os.path.splitext(os.path.basename(md.path))[0]

'''
Sequences of directory inputs
'''

@dataclass
class DirInputMetadata(SessionInputMetadata):
	path: Directory

	def __str__(self):
		return f'Directory {self.path}: session {self.session}, {self.size} samples'

class ParallelDirectoriesInputStage(ParallelSessionInputStage):

	@staticmethod
	def input_parameter() -> Parameter:
		return RangedDirectoryParameter(units=None, description='')

	def extract_name(self, md: DirInputMetadata) -> str:
		return os.path.basename(md.path)
