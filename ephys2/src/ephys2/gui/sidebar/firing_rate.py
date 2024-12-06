'''
Plot firing rates
'''
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt

import ephys2.gui.colors as gc
from ephys2.gui.types import *
from ephys2.lib.types import LVBatch
from ephys2.lib.singletons import global_metadata

class FiringRateWidget(GUIWidget, pg.GraphicsLayoutWidget):

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		pg.GraphicsLayoutWidget.__init__(self, *args, **kwargs)

		self.setBackground('w')
		self._plot = self.addPlot()
		self._plot.setMouseEnabled(x=False, y=False)
		self._plot.getViewBox().suggestPadding = lambda *_: 0
		self._bar = pg.BarGraphItem(x=range(5), height=range(5), width=1.0)
		self._plot.addItem(self._bar)
		self.subscribe_store('visible_data', self.updateData)

	def updateData(self):
		data = self.store['visible_data']
		if data.size > 0:
			tdelta = (data.time.max() - data.time.min()) / global_metadata['sampling_rate']
			lbs = np.unique(data.labels)
			rates = [
				(data.labels == lb).sum() / tdelta for lb in lbs
			]
			colors = gc.primary_brushes[lbs % gc.n_colors]
			self._bar.setOpts(x=range(len(rates)), height=rates, brushes=colors)
		else:
			self._bar.setOpts()

	def wheelEvent(self, evt):
		# Pass scroll to parent
		evt.ignore() 
