'''
Global profilers
'''

import pstats
import cProfile

from ephys2.lib.mpi import MPI

class Profiler:
	def __init__(self):
		self.profilers = dict()
		self.rank = MPI.COMM_WORLD.Get_rank()
		self._on = False

	@property
	def on(self):
		return self._on

	@on.setter
	def on(self, yes: bool):
		if yes and self.rank == 0:
			print('Ephys2 running with profiling enabled.')
		self._on = yes

	def start_step(self, name):
		if self._on and self.rank == 0:
			if not (name in self.profilers):
				self.profilers[name] = cProfile.Profile()
			self.profilers[name].enable()

	def stop_step(self, name):
		if self._on and self.rank == 0:
			self.profilers[name].disable()

	def print(self):
		if self._on and self.rank == 0:
			print('\nPROFILES:')
			for name, prof in self.profilers.items():
				print(f'Profile for {name}:')
				stats = pstats.Stats(prof).sort_stats('tottime')
				stats.print_stats(10)

profiler = Profiler()