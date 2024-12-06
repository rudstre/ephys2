'''
Widget for VBatch data
'''
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import pdb
import numpy as np

from ephys2.lib.types import *
from ephys2.gui.sidebar import *
from ephys2.gui.multibatch.widget import *

from .store import *

class VMultiBatchWidget(MultiBatchWidget):

	def __init__(self, store: GUIStore, *args, **kwargs):
		MultiBatchWidget.__init__(self, store, *args, **kwargs)
		self.subscribe_store('visible_data', self.update_summary_text)

	def update_summary_text(self):
		data = self.store['visible_data']
		self._summaryText.setText(f'datapoints: {data.size}; dimension: {data.ndim}')

