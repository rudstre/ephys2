'''
Viewer for benchmark results
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from typing import List
import os

from ephys2.pipeline.benchmark.intrinsic import *
from ephys2.pipeline.benchmark.extrinsic import *
from ephys2.gui.utils import *

from .intrinsic import *
from .extrinsic import *

class BenchmarkWidget(QtWidgets.QMainWindow):

	def set_files(self, filepaths: List[str]):
		assert len(filepaths) > 0
		benchmarks = []
		for path in filepaths:
			with open(path, 'r') as file:
				benchmarks.append(file.read())

		if 'ExtrinsicBenchmark' in benchmarks[0]:
			assert all('ExtrinsicBenchmark' in bm for bm in benchmarks)
			print('Showing extrinsic benchmarks')
			benchmarks = [ExtrinsicBenchmark.from_json(bm) for bm in benchmarks]
			assert all(bm.dataset == benchmarks[0].dataset for bm in benchmarks)
			self.setCentralWidget(ExtrinsicBenchmarkWidget(benchmarks))

		elif 'IntrinsicBenchmark' in benchmarks[0]:
			assert all('IntrinsicBenchmark' in bm for bm in benchmarks)
			print('Showing intrinsic benchmarks')
			benchmarks = [IntrinsicBenchmark.from_json(bm) for bm in benchmarks]
			assert all(bm.dataset == benchmarks[0].dataset for bm in benchmarks)
			self.setCentralWidget(IntrinsicBenchmarkWidget(benchmarks))

		else:
			show_error(f'Unrecognized benchmark file')