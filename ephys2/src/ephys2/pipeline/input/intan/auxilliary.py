'''
Utility class and methods for reading auxiliary data from Intan RHD2000 datasets.
'''

import numpy as np

from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, logger, global_state
from ephys2.lib.h5 import *
from ephys2.pipeline.input.base import *

class RHDAuxStage(ProcessingStage):

	@staticmethod
	def parameters(
			dio_chs: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
			aio_chs: List[int] = [1, 2, 3, 4, 5, 6]
		) -> Parameters:
		return {
			'aux_channels': MultiParameter(units=None, description='Analog and digital aux channels to save; set to [] to skip', options=[
				DictParameter(None, 'Digital aux channel declaration; stores times of lo->hi transitions', {
					'digital_in': MultiCategoricalParameter(None, '', dio_chs),
					'name': StringParameter(None, '')
				}),
				DictParameter(None, 'Analog aux channel declaration; stores aux samples at some downsampled rate', {
					'analog_in': MultiCategoricalParameter(None, '', aio_chs),
					'name': StringParameter(None, ''),
					'downsample': IntParameter('samples', 'Ratio at which to downsample analog inputs', 1, np.inf),
				})
			])
		}

	def initialize(self):
		# Whether auxiliary serializers are enabled
		self.digital_in = False
		self.analog_in = False

		super(type(self), self).initialize()

		assert 'session_splits' in global_metadata
		assert 'session_paths' in global_metadata
		assert len(global_metadata['session_splits']) == len(global_metadata['session_paths'])

		# Create serializers for auxiliary data as needed
		self.digital_chs = []
		self.digital_serializers = []
		self.analog_chs = []
		self.analog_serializers = []
		for aux_decl in self.cfg['aux_channels']:

			if 'digital_in' in aux_decl:
				assert self.cfg['batch_overlap'] == 0, 'nonzero batch_overlap not supported with aux channel persistence, for now'
				self.digital_chs = np.array(aux_decl['digital_in'], dtype=np.intp) # Digital is 0-indexed
				for i, path in enumerate(global_metadata['session_paths']):
					s = H5TMultiBatchSerializer(full_check=global_state.debug, rank=self.rank, n_workers=self.n_workers)
					s.initialize(os.path.join(path, f'session_{i}_{aux_decl["name"]}'))
					self.digital_serializers.append(s)

			if 'analog_in' in aux_decl:
				assert self.cfg['batch_overlap'] == 0, 'nonzero batch_overlap not supported with aux channel persistence, for now'
				self.analog_ds = aux_decl['downsample']
				self.analog_chs = np.array(aux_decl['analog_in'], dtype=np.intp) - 1 # Analog is 1-indexed
				for i, path in enumerate(global_metadata['session_paths']):
					s = H5SBatchSerializer(full_check=global_state.debug, rank=self.rank, n_workers=self.n_workers)
					s.initialize(os.path.join(path, f'session_{i}_{aux_decl["name"]}'))
					self.analog_serializers.append(s)

	def validate_aux_metadata(self, header: Optional[dict] = None):
		for aux_decl in self.cfg['aux_channels']:
			if 'digital_in' in aux_decl:
				if not (header is None):
					assert len(header['board_dig_in_channels']) > 0, 'No digital inputs were enabled in the header'
				self.dio_chs = np.array(aux_decl['digital_in'], dtype=np.intp)
				self.digital_in = True
			if 'analog_in' in aux_decl:
				if not (header is None):
					h_anains = [port['native_channel_name'] for port in header['aux_input_channels']]
					for ch in aux_decl['analog_in']:
						assert f'A-AUX{ch}' in h_anains, f'Aux analog input {ch} was not found in the enabled ones:\n\t{h_anains}'
				self.aio_chs = np.array(aux_decl['analog_in'], dtype=np.intp) - 1
				self.analog_in = True

	def capture_dio(self, md: InputMetadata, digital_data: npt.NDArray[np.uint16], time: np.ndarray, start_offset: int):
		# Save digital in
		if digital_data.size > 0:
			items = dict()
			for ch in self.digital_chs:
				# Indices of lo -> hi
				# Convention is that any leading 1 is ignored.
				mask = np.diff((digital_data & (1 << ch))) > 0
				items[str(ch)] = TBatch(
					time = time[(1 - start_offset):][mask], # Change times
					overlap = 0
				)
			self.digital_batches[md.session].append(TMultiBatch(items=items))

	def capture_aio(self, md: InputMetadata, analog_data: np.ndarray, time: np.ndarray, start_offset: int, fs: int):
		# Save analog in
		if analog_data.size > 0:
			analog_time = time
			analog_data = analog_data[start_offset:, self.analog_chs]
			if self.analog_ds > 1:
				mask = time % self.analog_ds == 0
				analog_time = analog_time[mask]
				analog_data = analog_data[mask]
			assert analog_time.shape[0] == analog_data.shape[0]
			self.analog_batches[md.session].append(SBatch(
				time = analog_time,
				data = analog_data,
				overlap = 0,
				fs = fs # Although analog data is downsampled, the timestamps reflect the original sampling rate.
			))

	def initialize_aux_batches(self):
		self.digital_batches = [
			TMultiBatch(items={str(ch): TBatch.empty() for ch in self.digital_chs})
			for _ in self.digital_serializers
		]
		self.analog_batches = [
			SBatch.empty(len(self.analog_chs), global_metadata['sampling_rate'])
			for _ in self.analog_serializers
		]

	def write_aux_batches(self):
		'''
		Serialize auxiliary data in chunks

		NOTE: this follows the principle of everyone writes once, every call.
		i.e. initialize_aux_batches() / write_aux_batches() should be called in pairs, 
		once per call during this stages's load() method
		'''
		for serializer, batch in zip(
				self.digital_serializers + self.analog_serializers, 
				self.digital_batches + self.analog_batches
			):
			serializer.write(batch)

	def finalize(self):
		# Persist final aux data
		if not (self.digital_serializers is None):
			for s in self.digital_serializers:
				s.serialize()
				s.cleanup()
				logger.print(f'Wrote digital out file: {s.out_path}')
		if not (self.analog_serializers is None):
			for s in self.analog_serializers:
				s.serialize()
				s.cleanup()
				logger.print(f'Wrote analog out file: {s.out_path}')

	def cleanup(self):
		# Clean up temporary files, for testing purposes
		for s in self.digital_serializers + self.analog_serializers:
			s.cleanup()