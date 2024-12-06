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

class WaveformWidget(GUIWidget, VLayoutWidget):
	'''
	Popup page to show on waveform selection (specialized to tetrodes)
	'''
	ypad = 0.1 # Percent padding in y-axis
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

		self.waveformCurves = [] # Selected curves
		self.hvWaveformCurve = pg.PlotCurveItem(pen='black') # Hovered curve
		self.hvWaveformCurve.setZValue(10)
		self.waveformPlot.addItem(self.hvWaveformCurve)

		self._dividers_added = False

		# Callbacks
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

		# Set hovered waveform
		ymax = 50
		if self.store['hovered'] is None:
			self.hvWaveformCurve.setData()
		else:
			y = data.data[self.store['hovered']]
			ymax = max(ymax, np.abs(y).max())
			self.hvWaveformCurve.setData(x, y)
				
		self._set_yrange(self.waveformPlot, ymax)

	def wheelEvent(self, evt):
		# Pass scroll to parent
		evt.ignore() 

	def _addSubplot(self):
		wc = pg.PlotCurveItem()
		wc.setZValue(5)
		self.waveformPlot.addItem(wc)
		self.waveformCurves.append(wc)

	@property
	def n_subplots(self) -> int:
		return len(self.waveformCurves)

	def _set_yrange(self, plot, ymax: float):
		ymax += self.ypad * ymax
		ymax = int(ymax) + 1
		yticks = [[(v, str(v)) for v in (-ymax, 0, ymax)]]
		plot.setYRange(-ymax, ymax)
		plot.getAxis('left').setTicks(yticks)
