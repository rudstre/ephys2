'''
MPI-aware logging 
'''
import sys
import warnings
from tqdm import tqdm
import io

from ephys2.lib.mpi import MPI

def format_warning(message, category, filename, lineno, line=None):
	return '%s: %s\n' % (category.__name__, message)

warnings.formatwarning = format_warning

class Logger:

	def __init__(self):
		self.rank = MPI.COMM_WORLD.Get_rank()
		self._verbose = False
		self._is_pytest = 'pytest' in sys.modules

	@property
	def verbose(self):
		return self._verbose or self._is_pytest

	@verbose.setter
	def verbose(self, yes: bool):
		if yes:
			self.print('Ephys2 running in verbose mode.')
		self._verbose = yes

	def debug(self, *args):
		if self.rank == 0 and self.verbose:
			print(*args, flush=True)

	def print(self, *args):
		if self.rank == 0:
			print(*args, flush=True)

	def warn(self, *args):
		if self.rank == 0:
			warnings.warn(*args)

	def pbar(self, total: int, description: str, unit: str) -> 'PBar':
		return PBar(total, description, unit)

logger = Logger()

class PBar:

	def __init__(self, total: int, description: str, unit: str):
		self.rank = MPI.COMM_WORLD.Get_rank()
		self.out = io.StringIO()
		self._pbar = tqdm(total=total, unit=unit, desc=description, file=self.out)

	def set(self, n: int):
		self._pbar.n = n
		self._pbar.refresh()
		logger.print(self.out.getvalue())

	def close(self):
		self._pbar.close()