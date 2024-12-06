'''
RHD viewer widget
'''
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication
import pyqtgraph as pg

from ephys2.gui.sbatch.widget import *

from .store import *

class RHDWidget(SBatchWidget):

	def _makeStore(self):
		return RHDStore()

	def _connectStore(self):
		super()._connectStore()
		self.store.subscribe('filepath', lambda: self.fileText.setText(f'File: {self.store["filepath"]}'))
		self.store.subscribe('N_x', lambda: self.nSamplesText.setText(f'Total # samples: {self.store["N_x"]}'))

	def _renderMain(self):
		super()._renderMain()
		self.fileText = QtWidgets.QLabel('')
		self.nSamplesText = QtWidgets.QLabel('')
		self.bottomLayout.addWidget(self.fileText)
		self.bottomLayout.addWidget(self.nSamplesText)

