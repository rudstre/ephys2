'''
Visualizer for class-average waveforms
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import os
import pdb
import numpy as np
import math

from ephys2.lib.settings import global_settings
from ephys2.lib.types import *
from ephys2.gui.utils import *
from ephys2.gui.types import *
import ephys2.gui.colors as gc

class AverageWaveformsWidget(GUIWidget, QtWidgets.QWidget):
	n_cols: int = 6
	n_rows: int = 3
	n_std: float = 3
	selected_grey = (240,240,240)

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		QtWidgets.QWidget.__init__(self, *args, **kwargs)
		self._graphWidget = pg.GraphicsLayoutWidget()
		self._graphWidget.setBackground('w')
		self._layout = VLayout()
		self._layout.addWidget(self._graphWidget)
		bottomWidget = QtWidgets.QWidget()
		bottomLayout = HLayout()
		bottomWidget.setLayout(bottomLayout)
		self._layout.addWidget(bottomWidget)
		bottomLayout.addStretch()
		bottomLayout.addWidget(QtWidgets.QLabel('Page:'))
		self._l_btn = IconButton('SP_ArrowLeft')
		self._page_label = QtWidgets.QLabel('0')
		self._r_btn = IconButton('SP_ArrowRight')
		bottomLayout.addWidget(self._l_btn)
		bottomLayout.addWidget(self._page_label)
		bottomLayout.addWidget(self._r_btn)
		self.setLayout(self._layout)

		# Plots
		self._plots = []
		self._curves = []
		self._locurves = []
		self._hicurves = []
		self._areacurves = []
		for row in range(self.n_rows):
			for col in range(self.n_cols):
				p = self._graphWidget.addPlot(row, col)
				p.setMouseEnabled(x=False, y=False)
				p.getViewBox().suggestPadding = lambda *_: 0
				p.hideAxis('bottom')
				c = pg.PlotCurveItem()
				c.setZValue(10)
				cl = pg.PlotCurveItem()
				ch = pg.PlotCurveItem()
				ca = pg.FillBetweenItem(cl, ch)
				p.addItem(c)
				p.addItem(ca)
				self._plots.append(p)
				self._curves.append(c)
				self._locurves.append(cl)
				self._hicurves.append(ch)
				self._areacurves.append(ca)

		# State
		self._page = 0
		self._is_editable = global_settings.gui_tag in ['LLVMultiBatch', 'SLLVMultiBatch']

		# Callbacks
		self._graphWidget.scene().sigMouseClicked.connect(self._on_click)
		self._l_btn.clicked.connect(lambda: self._move_page(-1))
		self._r_btn.clicked.connect(lambda: self._move_page(1))
		self.subscribe_store('selected_units', self.on_selection_change)
		self.subscribe_store('visible_data', self.updateData)

	@property
	def rend_n(self) -> int:
		return self.n_rows * self.n_cols

	def updateData(self):
		self._data = self.store['visible_data']
		self._labels = np.unique(self._data.labels)
		self._label_map = dict(zip(self._labels, np.arange(self._labels.size)))
		self._render()

	def _render(self):
		x = np.arange(self._data.data.shape[1])
		i = 0
		page_labels = self._labels[self.rend_n * self._page:self.rend_n * (self._page + 1)]
		while i < page_labels.size:
			lb = page_labels[i]
			c_i = lb % gc.n_colors
			X = self._data.data[self._data.labels == lb]
			avg = np.mean(X, axis=0)
			if isinstance(self._data, SLVBatch):
				std = np.sqrt(np.mean(self._data.variance[self._data.labels == lb], axis=0))
			else:
				std = np.std(X, axis=0)
			nstd = self.n_std * std
			ymax = np.abs(avg).max() + nstd.max()
			self._plots[i].setYRange(-ymax, ymax)
			self._curves[i].setData(x, avg, pen=gc.primary_pens_wide[c_i])
			self._locurves[i].setData(x, avg - nstd, pen=gc.secondary_pens[c_i])
			self._hicurves[i].setData(x, avg + nstd, pen=gc.secondary_pens[c_i])
			self._areacurves[i].setBrush(gc.secondary_brushes[c_i])
			i += 1

		while i < self.rend_n:
			self._curves[i].setData()
			self._locurves[i].setData()
			self._hicurves[i].setData()
			i += 1

		self.on_selection_change()

	def _on_click(self, evt):
		if not (self._is_editable and self.store['split_mode']):
			items = self._graphWidget.scene().items(evt.scenePos())
			plot_idx = None
			for i, p in enumerate(self._plots):
				if p in items:
					plot_idx = i 
					break
			if plot_idx != None: 
				lb_idx = self.rend_n * self._page + plot_idx
				if lb_idx < self._labels.size:
					label = self._labels[lb_idx]
					self.store.dispatch(GUIAction(tag='select', payload=label))

	def _move_page(self, delta: int):
		N = self._labels.size
		n_pages = math.ceil(N / self.rend_n)
		page = max(0, min(n_pages - 1, self._page + delta))
		if page != self._page:
			self._page = page
			self._page_label.setText(str(page))
			self._render()

	'''
	Public API 
	'''

	def on_selection_change(self):
		self.deselect_all()
		k_i, k_f = self._page * self.rend_n, (self._page + 1) * self.rend_n
		for lb in self.store['selected_units']:
			if lb in self._label_map:
				i = self._label_map[lb]
				if i >= k_i and i < k_f:
					self._plots[i % self.rend_n].getViewBox().setBackgroundColor(self.selected_grey)

	def deselect_all(self):
		for p in self._plots:
			p.getViewBox().setBackgroundColor('w')


