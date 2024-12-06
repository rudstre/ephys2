'''
Widget for LVBatch data
'''
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import os
import pdb
import numpy as np

from ephys2.lib.types import *
from ephys2.gui.types import *
from ephys2.gui.utils import *
from ephys2.gui.sidebar import *
from ephys2.gui.vbatch.widget import *
import ephys2.gui.colors as gc

from .store import *
from .avg_waveforms import *

class LVMultiBatchWidget(MultiBatchWidget):
	secondary_sample_size: int = 100

	def __init__(self, store: GUIStore, *args, **kwargs):
		MultiBatchWidget.__init__(self, store, *args, **kwargs)

		# Add aux views
		self._sidebar['Waveform'] = LabeledWaveformWidget(self.store)
		self._sidebar['ISI'] = ISIWidget(self.store)
		self._sidebar['Unit selector'] = UnitSelectorWidget(self.store)
		self._sidebar['Cross-correlation'] = CrossCorrWidget(self.store)
		# self._sidebar['Firing rate'] = FiringRateWidget(self.store)

		# Add aux tab
		self._avg_wvs = AverageWaveformsWidget(self.store)
		self._tabs.addTab(self._avg_wvs, 'Units')

		# Callbacks
		self.subscribe_store('visible_data', self.update_summary_text)

	def update_summary_text(self):
		data = self.store['visible_data']
		n_labels = np.unique(data.labels).size
		self._summaryText.setText(f'datapoints: {data.size}; dimension: {data.ndim}; clusters: {n_labels}')

