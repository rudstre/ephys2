'''
Widgets for visualizing single and multiple waveforms.
'''
from ast import Delete
from typing import List
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt

from ephys2.lib.types import VBatch, LVBatch
from ephys2.lib.singletons import global_metadata, rng
from ephys2.gui.widgets.multi_curve import *
from ephys2.gui.utils import *
from ephys2.gui.types import *
import ephys2.gui.colors as gc

class LabeledWaveformWidget(GUIWidget, VLayoutWidget):
	'''
	Popup page to show on waveform selection (specialized to tetrodes)
	'''
	ypad = 0.1 # Percent padding in y-axis
	secondary_sample_size: int = 100
	n_channels: int = 4
	default_height: int = 220

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		VLayoutWidget.__init__(self, *args, **kwargs)
		self._graphWidget = pg.GraphicsLayoutWidget()
		self._graphWidget.setBackground('w')
		self._graphWidget.setBackground('w')
		self._graphWidget.ci.layout.setContentsMargins(0, 0, 0, 0)
		self._graphWidget.ci.layout.setSpacing(0)
		self._graphWidget.wheelEvent = lambda evt: evt.ignore() # Pass scroll to parent
		self._layout.addWidget(self._graphWidget)

		self.waveformPlot = self._graphWidget.addPlot(0, 0)
		self.waveformPlot.setMouseEnabled(x=False, y=False)
		self.waveformPlot.getViewBox().suggestPadding = lambda *_: 0
		self.waveformPlot.hideAxis('bottom')

		self.waveformCurves = [] # Individual curves
		self.avgWaveformCurves = [] # Class average curves
		self.subWaveformCurves = [] # Class sample curves
		self.hvWaveformCurve = pg.PlotCurveItem(pen='black')
		self.hvWaveformCurve.setZValue(15)
		self.waveformPlot.addItem(self.hvWaveformCurve)

		# State
		self._dividers_added = False
		self._n_subplots = 0
		self._last_selected_labels = set()

		# Callbacks
		self.subscribe_store('selected_units', self.on_view_change)
		self.subscribe_store('hovered', self.on_view_change)

	def on_view_change(self):
		'''
		Renders the waveforms in `data` corresponding to `idxs`.
		Optionally renders `secondary` waveforms in the background.
		'''
		data = self.store['visible_data']
		x = np.arange(data.ndim) 

		if not self._dividers_added:
			for vline_pos in range(data.ndim // self.n_channels, data.ndim, data.ndim // self.n_channels):
				self.waveformPlot.addLine(x=vline_pos, pen='black')
			self._dividers_added = True
			self.waveformPlot.setXRange(0, x.max())

		# Set selected units
		labels = list(self.store['selected_units'])
		if labels != self._last_selected_labels:
			self._last_selected_labels = labels
			Nlabels = len(labels)
			while self._n_subplots < Nlabels:
				self._addSubplot()
			ymax = 50
			for i in range(self._n_subplots):
				if i < Nlabels:
					label = labels[i]
					y2 = data.data[data.labels == label]
					y3 = y2.mean(axis=0)
					ymax = max(ymax, np.abs(y3).max())
					K = min(y2.shape[0], self.secondary_sample_size)
					y2 = rng.choice(y2, size=K, axis=0, replace=False)
					self.subWaveformCurves[i].setData(x, y2, pen=gc.secondary_pens[label % gc.n_colors])
					self.avgWaveformCurves[i].setData(x, y3, pen=gc.primary_pens_wide[label % gc.n_colors])
				else:
					self.subWaveformCurves[i].setData()
					self.avgWaveformCurves[i].setData()
			self._set_yrange(self.waveformPlot, ymax)

		# Set hovered waveform
		if self.store['hovered'] is None:
			self.hvWaveformCurve.setData()
		else:
			self.hvWaveformCurve.setData(x, data.data[self.store['hovered']])
				
	def wheelEvent(self, evt):
		# Pass scroll to parent
		evt.ignore() 

	def _addSubplot(self):
		ac = pg.PlotCurveItem()
		ac.setZValue(5)
		self.waveformPlot.addItem(ac)
		self.avgWaveformCurves.append(ac)
		sc = MultiCurvePlotter(self.waveformPlot, self.secondary_sample_size)
		self.subWaveformCurves.append(sc)
		self._n_subplots += 1

	def _set_yrange(self, plot, ymax: float):
		ymax += self.ypad * ymax
		ymax = int(ymax) + 1
		yticks = [[(v, str(v)) for v in (-ymax, 0, ymax)]]
		plot.setYRange(-ymax, ymax)
		plot.getAxis('left').setTicks(yticks)
