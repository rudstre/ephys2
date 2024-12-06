'''
Processing stage for summarizing & downsampling clustered data
'''
import numpy as np
import numpy.typing as npt
import math

from ephys2.lib.types import *
from ephys2.lib.singletons import rng, global_state

class SummarizeStage(ProcessingStage):

	@staticmethod
	def name() -> str:
		return 'summarize'

	def type_map(self) -> Dict[type, type]:
		return {LLVMultiBatch: SLLVMultiBatch}

	@staticmethod
	def parameters() -> Parameters:
		return {
			'downsample_ratio': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Maximum rate at which data is downsampled, per-class'
			),
			'downsample_data_method': CategoricalParameter(
				categories = ['mean', 'median'],
				units = None,
				description = 'Method for downsampling the waveforms'
			),
			'downsample_time_method': CategoricalParameter(
				categories = ['mean', 'median'],
				units = None,
				description = 'Method for downsampling the timestamps'
			),
			'isi_subsamples': IntParameter(
				start = 1,
				stop = np.inf,
				units = None,
				description = 'Maximum number of subsamples of the ISI distribution to keep from each downsampled region; higher produces a better sampling of the true ISI distribution  at a larger storage cost'
			),
		}

	def process(self, data: LLVMultiBatch) -> SLLVMultiBatch:
		items = dict()
		R = self.cfg['downsample_ratio']
		ND = self.cfg['isi_subsamples']

		for item_id, item in data.items.items():
			# Check consistency of the data dimensions
			B = item.block_size
			assert global_state.load_overlap % B == 0, f'Overlap must be a multiple of block_size: {B} used in clustering. Check your checkpoint / load stage.'
			assert global_state.load_batch_size % B == 0, f'Load batch size must be a multiple of the block size: {B} used in clustering. Check your checkpoint / load stage.'
			
			# Compute summary statistics per-block
			O = item.overlap
			item_time = item.time[O:] # Remove any overlap prior to summarization
			item_data = item.data[O:]
			item_labels = item.labels[O:]
			N = item_time.size
			M = item.ndim
			summary = SLVBatch.empty(M, ND, R)
			item_indices = global_state.load_index - global_state.load_start + O + np.arange(N, dtype=np.intp) # Get indices of the data in the original dataset

			for k in range(math.ceil(N / B)):
				window = slice(k*B, (k+1)*B)
				btime = item_time[window]
				bdata = item_data[window]
				blabels = item_labels[window]
				bindices = item_indices[window]

				stime = []
				sdata = []
				slabels = []
				svariance = []
				sdifftime = []
				sindices = []

				for lb in np.unique(blabels):
					lmask = blabels == lb
					ltime = btime[lmask]
					ldata = bdata[lmask]
					lindices = bindices[lmask]
					NL = ltime.size

					for r in range(math.ceil(NL / R)):
						rwindow = slice(r*R, (r+1)*R)
						rtime = ltime[rwindow]
						rdata = ldata[rwindow]
						rindices = np.full(R, -1) # Convention is to store -1 for missing indices
						rindices[:rtime.size] = lindices[rwindow]

						stime.append(self.downsample_time(rtime))
						sdata.append(self.downsample_data(rdata))
						slabels.append(lb)
						svariance.append(rdata.var(axis=0))
						sdifftime.append(self.downsample_isi(rtime))
						sindices.append(rindices) 

				# Result is sorted by time
				stime = np.array(stime, dtype=np.int64)
				idx = np.argsort(stime)
				slvb = SLVBatch(
					time = stime[idx],
					data = np.vstack(sdata)[idx],
					labels = np.array(slabels, dtype=np.int64)[idx],
					variance = np.vstack(svariance)[idx],
					difftime = np.vstack(sdifftime)[idx],
					indices = np.vstack(sindices)[idx],
					overlap = 0
				)

				summary.append(slvb)

			items[item_id] = SLLVBatch.from_llvb(item, summary)

		return SLLVMultiBatch(items=items)

	def downsample_data(self, data: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
		'''
		This assumes data is NxM with N >= 1
		'''
		method = self.cfg['downsample_data_method']
		if method == 'mean':
			return np.mean(data, axis=0)
		elif method == 'median':
			return np.median(data, axis=0)
		else:
			raise ValueError(f'Unknown downsample_method: {method}')

	def downsample_time(self, time: npt.NDArray[np.int64]) -> int:
		'''
		This assumes len(time) is N with N >= 1
		'''
		method = self.cfg['downsample_time_method']
		if method == 'mean':
			return int(np.rint(np.mean(time)))
		elif method == 'median':
			return np.median(time)
		else:
			raise ValueError(f'Unknown downsample_method: {method}')

	def downsample_isi(self, time: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
		'''
		This assumes len(time) is N with N >= 1
		If time is insufficiently large, isi is padded with -1 and intended to be filtered in postprocessing.
		'''
		N = self.cfg['isi_subsamples']
		isi = np.diff(time)
		if isi.size > N:
			return rng.choice(isi, size=N, replace=False)
		elif isi.size < N:
			return np.hstack((isi, np.full(N - isi.size, -1)))
		return isi


