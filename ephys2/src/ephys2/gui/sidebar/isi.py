'''
Widgets for visualizing interspike interval.
'''
from typing import List
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
from scipy.stats import gaussian_kde

from ephys2.lib.types import *
from ephys2.lib.array import safe_hstack
from ephys2.lib.singletons import global_metadata, rng
from ephys2.gui.utils import *
from ephys2.gui.types import *
import ephys2.gui.colors as gc
from ephys2.lib.profile import profiling
from ephys2.lib.settings import global_settings

class ISIWidget(GUIWidget, VLayoutWidget):
	kde_points = 400
	ref_period = 1.5
	x_extent = 100000
	x_offset = 1e-2
	scatter_width = 2
	max_sample_size = 2000
	default_height = 350

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		VLayoutWidget.__init__(self, *args, **kwargs)
		# Plot
		self._graphWidget = pg.GraphicsLayoutWidget()
		self._graphWidget.setBackground('w')
		self._graphWidget.ci.layout.setContentsMargins(0, 0, 0, 0)
		self._graphWidget.ci.layout.setSpacing(0)
		self._graphWidget.wheelEvent = lambda evt: evt.ignore() # Pass scroll to parent
		self._plot = self._graphWidget.addPlot()
		self._plot.setMouseEnabled(x=False, y=False)
		self._plot.setLabel('left', 'Frequency')
		self._plot.setLabel('bottom', 'ISI', units='log10(ms)')
		self._plot.setXRange(np.log10(self.x_offset), np.log10(self.x_extent))
		self._vline = pg.InfiniteLine(pos=np.log10(self.ref_period), pen='black')
		self._plot.addItem(self._vline)

		# Curves
		self._curves = []
		self._scatters = []
		self._addSubplot()

		# Layout
		self._layout.addWidget(self._graphWidget)
		bottomWidget = HLayoutWidget()
		bottomWidget._layout.addWidget(QtWidgets.QLabel(f'Refractory period: {self.ref_period} ms'))
		self._layout.addWidget(bottomWidget)

		# Listeners
		self.subscribe_store('visible_data', self.updateData)
		self.subscribe_store('selected_units', self.updateData)

	def updateData(self):
		data = self.store['visible_data']

		# No labels - ISI is computed over the full dataset
		if not (isinstance(data, LVBatch) or isinstance(data, SLVBatch)):
			self.setIsi(np.diff(data.time), self._scatters[0], self._curves[0], 0)

		# Labels - ISI is computed individually for units
		else:
			labels = list(self.store['selected_units'])
			nlabels = len(labels)
			while self.n_subplots < len(labels):
				self._addSubplot()

			for i in range(self.n_subplots):
				curve, scatter = self._curves[i], self._scatters[i]
				if i < nlabels:
					if isinstance(data, SLVBatch):
						isi = data.difftime[data.labels == labels[i]].ravel()
						self.setIsi(isi, scatter, curve, labels[i])
					elif isinstance(data, LVBatch):
						isi = np.diff(data.time[data.labels == labels[i]])
						self.setIsi(isi, scatter, curve, labels[i])
				else:
					self.setEmpty(scatter, curve)

	def setIsi(self, isi: npt.NDArray[np.int64], scatter: pg.ScatterPlotItem, curve: pg.PlotCurveItem, lbl: int):
		# Set ISI without any checks
		isi = isi[isi > 0]
		if isi.size > 1: # KDE requires at least 2 points
			isi = isi / (global_metadata['sampling_rate'] / 1000)
			isi = np.log10(isi + self.x_offset)
			if isi.size > self.max_sample_size:
				isi = rng.choice(isi, size=self.max_sample_size, replace=False)
			kde_x = np.linspace(np.log10(self.x_offset), np.log10(self.x_extent), self.kde_points)
			density = gaussian_kde(isi)
			kde_y = density(kde_x)
			curve.setData(kde_x, kde_y, pen=gc.primary_pens[lbl % gc.n_colors], brush=gc.secondary_brushes[lbl % gc.n_colors])
			scatter.setData(isi, np.zeros(isi.size), pen=gc.secondary_pens[lbl % gc.n_colors])
		else:
			self.setEmpty(scatter, curve)

	def setEmpty(self, scatter: pg.ScatterPlotItem, curve: pg.PlotCurveItem):
		curve.setData()
		scatter.setData()

	def _addSubplot(self):
		c = pg.PlotCurveItem(fillLevel=0)
		s = pg.ScatterPlotItem(size=self.scatter_width)
		self._plot.addItem(c)
		self._plot.addItem(s)
		self._curves.append(c)
		self._scatters.append(s)

	@property
	def n_subplots(self) -> int:
		return len(self._curves)
