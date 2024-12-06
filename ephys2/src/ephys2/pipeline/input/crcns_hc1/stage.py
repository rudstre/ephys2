'''
Load the crcns_hc1 datasets. 
These are single-cell intracellular-extracellular pair recordings.
Automatically downloads data from: https://crcns.org/data-sets/hc/hc-1/about
'''
import os
import requests
from tqdm import tqdm
from zipfile import ZipFile
from xml.etree import ElementTree

import ephys2.data
import ephys2._cpp
from ephys2.lib.types import *
from ephys2.lib.singletons import logger
from ephys2.pipeline.input.base import *
from ephys2.pipeline.input.ground_truth import *
from ephys2.pipeline.preprocess.iirfilter import BandpassStage

@dataclass
class HC1Metadata(InputMetadata):
	xml_path: ROFilePath
	data_path: ROFilePath
	n_bytes: int # N bytes per measurement
	n_channels: int
	fs: int # Sampling rate
	ec_indices: npt.NDArray

class CRCNS_HC1Stage(GroundTruthInputStage):
	URL = 'https://portal.nersc.gov/project/crcns/download/index.php'
	download_chunk_size = 1024
	gt_padding = 4 # ms padding around ground-truth data to load input

	@staticmethod
	def name() -> str:
		return 'crcns_hc1'

	def output_type(self) -> type:
		return SBatch

	@staticmethod
	def parameters() -> Parameters:
		path = ephys2.data.get_path('hc1_filelist.txt')
		with open(path, 'r') as file:
			filelist = file.readlines()[5:-8]
			datasets = [f.split('.zip')[0][6:] for f in filelist]

		return GroundTruthInputStage.parameters() | {
			'crcns_username': StringParameter(
				units = None,
				description = 'Username to download data from CRCNS'
			),
			'crcns_password': StringParameter(
				units = None,
				description = 'Password to download data from CRCNS'
			),
			'data_directory': DirectoryParameter(
				units = None,
				description = 'Eirectory either containing CRCNS data or where data can be downloaded'
			),
			'dataset': CategoricalParameter(
				categories = datasets,
				units = None,
				description = 'CRCNS-HC1 dataset to use'
			),
			'session': StringParameter(
				units = None,
				description = 'Session within the dataset'
			),
			'ec_channels': ListParameter(
				element = IntParameter(start=0, stop=np.inf, units=None, description=''),
				units = None,
				description = 'Channels containing extracellular recordings'
			),
			'ic_channel': IntParameter(
				start = 0,
				stop = np.inf,
				units = None,
				description = 'Channel containing intracellular recording'
			),
			'ic_threshold': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'μV',
				description = 'Absolute threshold for detection of intracellular spike'
			),
			'ic_refractory': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'ms',
				description = 'Refractory period for intracellular spike detection'
			),
			'ic_highpass': FloatParameter(
				start = 0,
				stop = np.inf,
				units = 'Hz',
				description = 'High-pass frequency for intracellular channel'
			),
		}

	def make_metadata(self) -> HC1Metadata:
		''' 
		Acquire data, extract ground-truth, build metadata
		'''
		dset = self.cfg['dataset']
		Directory = self.cfg['data_directory']

		# Download data as needed
		if self.rank == 0:
			if os.path.isdir(f'{Directory}/{dset}'):
				logger.print(f'Dataset {dset} found')
			else:
				logger.print(f'Dataset {dset} not found, downloading to {Directory}/{dset}...')
				self.download(dset)

		# Wait for all the data to be downloaded
		self.comm.Barrier()

		# Read session metadata
		xml_path = f'{Directory}/{dset}/{dset}{self.cfg["session"]}.xml'
		data_path = f'{Directory}/{dset}/{dset}{self.cfg["session"]}.dat'
		xml_root = ElementTree.parse(xml_path).getroot()
		acq_root = xml_root.find('acquisitionSystem')
		n_bytes = int(acq_root.find('nBits').text) // 8
		n_channels = int(acq_root.find('nChannels').text)
		fs = int(acq_root.find('samplingRate').text)
		n_samples = os.path.getsize(data_path) // (n_bytes * n_channels)

		return HC1Metadata(
			size = n_samples,
			start = self.cfg['start'],
			stop = self.cfg['stop'],
			offset = 0,
			xml_path = xml_path,
			data_path = data_path,
			n_bytes = n_bytes,
			n_channels = n_channels,
			fs = fs,
			ec_indices = np.array(self.cfg['ec_channels'], dtype=np.int64)
		)

	def download(self, dataset: str):
		'''
		Download a dataset to the configured data_directory.
		Based on crcnsget, https://github.com/neuromusic/crcnsget
		'''
		out_dir = self.cfg["data_directory"]
		out_zip = f'{out_dir}/{dataset}.zip'
		params = {
			'username': self.cfg['crcns_username'],
			'password': self.cfg['crcns_password'],
			'fn': f'hc-1/Data/{dataset}.zip',
			'submit': 'Login',
		}
		with requests.Session() as sess:
			resp = sess.post(self.URL, data=params, stream=True)
			total_size = int(resp.headers.get('content-length', 0))
			with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
				with open(out_zip, 'wb') as file:
					for chunk in resp.iter_content(chunk_size=self.download_chunk_size):
						if chunk:
							file.write(chunk)
							pbar.update(len(chunk))

		# Unzip the data
		with ZipFile(out_zip, 'r') as zfile:
			zfile.extractall(out_dir)
		os.remove(out_zip)

		logger.print(f'{dataset} finished.')

	def write_ground_truth(self, md: HC1Metadata, path: RWFilePath):
		if self.rank == 0:
			filter_stage = BandpassStage({
				'order': 2,
				'highpass': self.cfg['ic_highpass'],
				'lowpass': np.inf,
				'Rp': 0.2, # Maximum ripple in the passband (dB)
		    'Rs': 100, # Minimum attenuation in the stopband (dB)
		    'type': 'ellip', # Filter type (options: `ellip`, `cheby1`, `cheby2`), see https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.iirdesign.html
		    'padding_type': 'odd', # Signal extension method (others supported: `odd`, `even`)
		    'padding_length': 1000, # Edge padding
			})

			N = md.stop - md.start
			offset = md.start * md.n_bytes * md.n_channels
			count = N * md.n_channels
			data = np.fromfile(md.data_path, offset=offset, count=count, dtype=np.int16).astype(np.float32)
			data.shape = (N, md.n_channels)
			ic_data = data[:, self.cfg['ic_channel']]
			ic_times = np.arange(md.start, md.stop, dtype=np.int64)

			# Run highpass
			ic_data = filter_stage.process(SBatch(time=ic_times, data=ic_data[:, np.newaxis], overlap=0, fs=md.fs))
			ic_data = np.squeeze(ic_data.data)

			# Detect intracellular spikes
			ic_refr = int(self.cfg['ic_refractory'] * 1000 / md.fs)
			ic_times = ephys2._cpp.detect_channel(ic_times, ic_data, self.cfg['ic_threshold'], ic_refr)

			with h5py.File(path, 'w') as gt_file:
				gt_file.attrs['tag'] = 'LTMultiBatch'
				gt_dir = gt_file.create_group('0') # Intracellular recording is a single unit
				gt_dir.create_dataset('time', data=ic_times)
				gt_dir.create_dataset('labels', data=np.ones(ic_times.size, dtype=np.int64))

	def load(self, start: int, stop: int) -> SBatch:
		md = self.metadata
		N = stop - start
		offset = start * md.n_bytes * md.n_channels
		count = N * md.n_channels
		data = np.fromfile(md.data_path, offset=offset, count=count, dtype=np.int16).astype(np.float32)
		data.shape = (N, md.n_channels)
		data = data[:, md.ec_indices]
		overlap = max(0, self.cfg['batch_overlap'] - (self.cfg['batch_size'] - data.shape[0])) # Effective overlap
		return SBatch(
			time = np.arange(start, stop),
			data = data,
			overlap = overlap,
			fs = md.fs
		)
