'''
Global state of the application (per-process)
Not stored or read from HDF5 data
'''
from typing import Optional

from .logger import logger

class State:

	def __init__(self):
		self._last_h5 = None
		self.load_index = 0
		self.load_start = 0
		self.load_size = None
		self.load_overlap = 0
		self.load_batch_size = 0
		self._debug = False

	@property
	def last_h5(self) -> Optional[str]:
		return self._last_h5

	@last_h5.setter
	def last_h5(self, p: str):
		logger.print('Set global H5 path:', p)
		self._last_h5 = p

	@property
	def debug(self) -> bool:
		return self._debug

	@debug.setter
	def debug(self, p: bool):
		if p:
			logger.print('Ephys2 running in debug mode.')
		self._debug = p

global_state = State()