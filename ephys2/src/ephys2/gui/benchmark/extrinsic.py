'''
Viewer for extrinsic benchmarks
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from typing import List

from ephys2.pipeline.benchmark.extrinsic import *


class ExtrinsicBenchmarkWidget(QtWidgets.QWidget):

	def __init__(self, benchmarks: List[ExtrinsicBenchmark], *args, **kwargs):
		super().__init__(*args, **kwargs)