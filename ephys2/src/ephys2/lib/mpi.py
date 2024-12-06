'''
Wrapper around MPI for MPI-incompatible environments
'''
import warnings
import sys
import signal
import traceback
from typing import Callable

from .settings import global_settings

class DummyMPI:
	'''
	Emulate the MPI wrapper in a single-process environment (e.g. in the GUI)
	'''
	@property
	def COMM_WORLD(self) -> 'DummyMPIComm':
		return DummyMPIComm()

class DummyMPIComm:

	def Get_size(self) -> int:
		return 1

	def Get_rank(self) -> int:
		return 0

	def Barrier(self):
		return

	def Abort(self):
		return 
	
	def bcast(self, data, root=0):
		return data

if global_settings.mpi_enabled:
	try:
		from mpi4py import MPI
	except ImportError:
		# Enable use of this stage if MPI is not available
		warnings.warn('MPI not available, running in single-threaded mode')
		MPI = DummyMPI()
else:
	print('Running without MPI.')
	MPI = DummyMPI()

'''
Register signal handlers
'''

def mpi_sigterm(signum, frame):
	raise KeyboardInterrupt

signal.signal(signal.SIGTERM, mpi_sigterm)

'''
Run functions with MPI-aware exception handling
'''

def mpi_try(func: Callable, *args, **kwargs):
	try:
		func(*args, **kwargs)
	except:
		traceback.print_exc()
		MPI.COMM_WORLD.Abort()
		raise