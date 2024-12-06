'''
Profiling utilities
'''

import pstats
import cProfile
from contextlib import contextmanager

@contextmanager
def profiling(on=True, sort='cumtime'):
	if on:
		prof = cProfile.Profile()
		prof.enable()
		yield
		prof.disable()
		stats = pstats.Stats(prof).sort_stats(sort)
		stats.print_stats(20)
	else:
		yield