'''
Cross-correlation widget
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
import pdb

from ephys2.gui.utils import *
from ephys2.gui.types import *
from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata, rng


class CrossCorrWidget(GUIWidget, QtWidgets.QWidget):
	bins = 50
	window = 200 # ms
	max_sample_size = 2000

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		QtWidgets.QWidget.__init__(self, *args, **kwargs)
		self._lb1 = None
		self._lb2 = None

		# Layout
		self._vLayout = VLayout()
		self.setLayout(self._vLayout)

		# Selectors
		selectorWidget = HLayoutWidget()
		self._unit1cb = pg.ComboBox()
		self._unit2cb = pg.ComboBox()
		selectorWidget._layout.addWidget(QtWidgets.QLabel('Selected units:'))
		selectorWidget._layout.addWidget(self._unit1cb)
		selectorWidget._layout.addWidget(QtWidgets.QLabel('vs'))
		selectorWidget._layout.addWidget(self._unit2cb)
		self._vLayout.addWidget(selectorWidget)

		# Plot
		self._graphWidget = pg.GraphicsLayoutWidget()
		self._graphWidget.setBackground('w')
		self._graphWidget.wheelEvent = lambda evt: evt.ignore() # Pass scroll to parent
		self._graphWidget.ci.layout.setContentsMargins(0, 0, 0, 0)
		self._graphWidget.ci.layout.setSpacing(0)
		self._plot = self._graphWidget.addPlot()
		self._plot.setMouseEnabled(x=False, y=False)
		self._plot.setLabel('left', 'Count')
		self._plot.setLabel('bottom', 'Time lag', units='ms')
		self._curve = pg.PlotDataItem(stepMode='center', fillLevel=0, brush='orange')
		self._plot.addItem(self._curve)
		self._vLayout.addWidget(self._graphWidget)

		# Callbacks
		self._unit1cb.currentIndexChanged.connect(lambda _: self._updateLabels())
		self._unit2cb.currentIndexChanged.connect(lambda _: self._updateLabels())
		self.subscribe_store('selected_units', self.on_selection_update)
		self.subscribe_store('visible_data', self._redraw)

	def on_selection_update(self):
		selected = list(self.store['selected_units'])
		items = [str(lb) for lb in selected]
		self._unit1cb.setItems(items)
		self._unit2cb.setItems(items)
		dirty = False
		if len(selected) == 0:
			self._lb1 = None
			self._lb2 = None
			dirty = True
		else:
			if not (self._lb1 in selected):
				self._lb1 = selected[0]
				dirty = True
			if self._lb2 == self._lb1 and len(selected) >= 2:
				self._lb2 = selected[1]
				dirty = True
			elif not (self._lb2 in selected):
				self._lb2 = selected[1 % len(selected)]
				dirty = True
			self._unit1cb.setValue(str(self._lb1))
			self._unit2cb.setValue(str(self._lb2))
		if dirty:
			self._redraw()

	def _redraw(self):
		if not (self._lb1 is None or self._lb2 is None):
			data = self.store['visible_data']
			times1 = data.time[data.labels == self._lb1].astype(np.int64)
			times2 = data.time[data.labels == self._lb2].astype(np.int64)
			if times1.size > self.max_sample_size:
				times1 = rng.choice(times1, size=self.max_sample_size, replace=False)
			if times2.size > self.max_sample_size:
				times2 = rng.choice(times2, size=self.max_sample_size, replace=False)
			dists = np.subtract.outer(times1, times2).ravel() * 1000 / global_metadata['sampling_rate']
			if self._lb1 == self._lb2:
				dists = dists[dists != 0]
			hist, bins = np.histogram(dists, bins=self.bins, range=(-self.window/2, self.window/2))
			self._curve.setData(bins, hist)
		else:
			self._curve.setData()

	def _updateLabels(self):
		self._lb1 = self._unit1cb.value()
		if self._lb1 != None:
			self._lb1 = int(self._lb1)
		self._lb2 = self._unit2cb.value()
		if self._lb2 != None:
			self._lb2 = int(self._lb2)
		self._redraw()

