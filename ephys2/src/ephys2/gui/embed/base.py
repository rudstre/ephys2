'''
Abstract widget for embedding data in 2 visible dimensions (time vs data or data vs data)
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import QPointF, Qt
from qtpy.QtWidgets import QApplication
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional

from ephys2.lib.settings import global_settings
from ephys2.lib.types import *
from ephys2.lib.array import *
from ephys2.lib.profile import profiling
from ephys2.gui.types import *
from ephys2.gui.utils import *
from ephys2.gui.widgets.toggle import QToggle
from ephys2.gui.widgets.polygon import SelectionPolygon
from ephys2.gui.widgets.divider import SelectionDivider
import ephys2.gui.colors as gc

class EmbedWidget(GUIWidget, VLayoutWidget, metaclass=QtABCMeta):
	scatter_brush = (255, 0, 0)
	scatter_pt_size = 3
	scatter_pt_size_hovered = 5
	ax_x_padding = 0.1
	ax_y_padding = 0.1
	auto_bounds = False # Disable automatic bounds setting
	step_percent: float = 0.1 # Step size when using navigation shortcuts
	zoom_percent: float = 0.1 # Zoom in or out percentage
	
	@staticmethod
	@abstractmethod
	def axisMap() -> Dict[str, int]:
		'''
		Get options for the 1 dimensional embedding.
		'''
		pass

	@staticmethod
	@abstractmethod
	def ndim() -> int:
		'''
		Return dimension of the embedding
		'''
		return 

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		VLayoutWidget.__init__(self, *args, **kwargs)

		# Data instance variables
		self._data = None
		self._xs = None
		self._ys = None
		self._on_split = lambda mask, inclusion: None
		self._brushes = None
		self._last_highlighted = set()
		self._is_labeled = global_settings.gui_tag in ['LVMultiBatch', 'LLVMultiBatch', 'SLLVMultiBatch']
		self._is_editable = global_settings.gui_tag in ['LLVMultiBatch', 'SLLVMultiBatch']
		self._split_on = False
		self._split_nd = self.ndim()

		# Configure axis selector widget
		self._axWidget = HLayoutWidget()
		N = self.ndim()
		assert N in [1, 2], 'Dimension of embedding must be 1 or 2 currently.'
		options = list(self.axisMap().keys())
		self._axSelectors = []
		for i in range(N):
			if i > 0:
				self._axWidget._layout.addWidget(QtWidgets.QLabel('vs'))
			cb = pg.ComboBox() 
			cb.addItems(options)
			cb.setCurrentIndex(i) # By default select different options
			cb.currentIndexChanged.connect(lambda _: self._updatePlot())
			self._axSelectors.append(cb)
			self._axWidget._layout.addWidget(cb)
		self._axWidget._layout.addStretch()

		# Configure main plot widget
		self._graphWidget = pg.GraphicsLayoutWidget()
		self._graphWidget.setBackground('w')
		# self._graphWidget.wheelEvent = lambda evt: evt.ignore() # Pass scroll to parent
		self._graphWidget.ci.layout.setContentsMargins(0, 0, 0, 0)
		self._graphWidget.ci.layout.setSpacing(0)
		self._plot = self._graphWidget.addPlot()
		self._scatter = pg.ScatterPlotItem(
			size=self.scatter_pt_size, 
			brush=self.scatter_brush, 
			hoverable=True, 
			pen=None, 
			tip=None,
			hoverPen=(None if self._is_labeled else 'blue'),
			# dynamicRangeLimit=False,
			# skipFiniteCheck=True
		)
		self._plot.addItem(self._scatter)

		# Splitting widgets
		self._splitWidget = HLayoutWidget()
		self._splitWidget.addStyle('background-color: red;')
		self._splitWidget._layout.setContentsMargins(2, 2, 2, 2)
		self._splitWidget._layout.addWidget(WhiteLabel('Split mode'))
		self._ndToggle = None
		self._applysplitbtn = PushButton('Apply')
		self._applysplitbtn.setEnabled(False)
		self._cancelsplitbtn = PushButton('Cancel')
		self._resetsplitbtn = PushButton('Reset')
		if self.ndim() == 1:
			self._ndToggle = QToggle()
			self._ndToggle.stateChanged.connect(self.on_split_nd_update)
			self._splitWidget._layout.addWidget(WhiteLabel('(1D'))
			self._splitWidget._layout.addWidget(self._ndToggle)
			self._splitWidget._layout.addWidget(WhiteLabel('2D)'))
		self._splitWidget._layout.addStretch()
		self._splitWidget._layout.addWidget(self._resetsplitbtn)
		self._splitWidget._layout.addWidget(self._applysplitbtn)
		self._splitWidget._layout.addWidget(self._cancelsplitbtn)
		self._cancelsplitbtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='reset_view')))
		self._applysplitbtn.clicked.connect(self.on_split_apply)
		self._resetsplitbtn.clicked.connect(self.on_split_reset)

		# Splitting ROIs
		self._divider = SelectionDivider(self._plot)
		self._divider.complete.connect(self.on_split_complete)
		self._polygon = SelectionPolygon(self._plot)
		self._polygon.complete.connect(self.on_split_complete)

		# Configure mouse interaction
		self._scatter.sigHovered.connect(self.mouseHovered)
		self.on_split_mode_update(force_update=True) 

		# Configure layout
		self._layout.addWidget(self._splitWidget)
		self._layout.addWidget(self._axWidget)
		self._layout.addWidget(self._graphWidget)
		self._splitWidget.hide()

		# Callbacks
		self.subscribe_store('visible_data', self.updateData)
		self.subscribe_store('hovered', self.on_highlight_change)
		if self._is_labeled:
			self.subscribe_store('selected_units', self.on_highlight_change)
		if self._is_editable:
			self.subscribe_store('split_mode', self.on_split_mode_update)

	@abstractmethod
	def embed(self, data: VBatch, *axes: List[int]) -> Tuple[npt.NDArray, npt.NDArray]:
		'''
		Embed the data in two dimensions.
		'''
		pass

	def _updatePlot(self):
		# Update scatter plot
		if not (self._data is None):
			axMap = self.axisMap()
			axes = [axMap[cb.currentText()] for cb in self._axSelectors]
			xs, ys = self.embed(self._data, *axes)
			self._xs, self._ys = xs, ys
			if isinstance(self._data, LVBatch):
				# Render labels if data is labeled
				self._brushes = gc.primary_brushes[self._data.labels % gc.n_colors]
				self._scatter.setData(xs, ys, brush=self._brushes, size=self._sizes)
			else:
				self._scatter.setData(xs, ys)
			if self.auto_bounds and xs.size > 0:
				xmin, xmax = xs.min(), xs.max()
				dx = xmax - xmin
				xmin -= dx * self.ax_x_padding
				xmax += dx * self.ax_x_padding
				ymin, ymax = ys.min(), ys.max()
				dy = ymax - ymin
				ymin -= dy * self.ax_y_padding
				ymax += dy * self.ax_y_padding
				self._plot.setXRange(xmin, xmax)
				self._plot.setYRange(ymin, ymax)

	''' Public API ''' 

	@property
	def on_split(self):
		return self._on_split

	@on_split.setter
	def on_split(self, func):
		self._on_split = func

	def updateData(self):
		self._data = self.store['visible_data']
		self._orig_sizes = np.full(self._data.size, self.scatter_pt_size)
		self.update_sizes()
		self._updatePlot()

	def on_highlight_change(self):
		if self._is_labeled and not (self._data is None):
			hovered = self.store['hovered']
			hovered = [] if hovered is None else [hovered]
			labels = self.store['visible_data'].labels
			highlighted = set([labels[i] for i in hovered]) | self.store['selected_units']
			if self._last_highlighted != highlighted:
				self._last_highlighted = highlighted
				self.update_sizes()
				self._scatter.setSize(self._sizes)

	def update_sizes(self):
		self._sizes = self._orig_sizes.copy()
		for label in self._last_highlighted:
			self._sizes[self._data.labels == label] = self.scatter_pt_size_hovered

	def translate_view(self, dx_percent: float, dy_percent: float):
		self.transform_view(dx_percent, dy_percent, 1)

	def zoom_view(self, dx_percent: float, dy_percent: float):
		self.transform_view(dx_percent, dy_percent, -1)

	def transform_view(self, dx_percent: float, dy_percent: float, sign: int):
		assert sign in [-1, 1]
		((xmin, xmax), (ymin, ymax)) = self._plot.viewRange()
		if dx_percent != 0:
			dx = xmax - xmin
			xmin += dx * dx_percent
			xmax += sign * dx * dx_percent
			self._plot.setXRange(xmin, xmax, padding=0)
		if dy_percent != 0:
			dy = ymax - ymin
			ymin += dy * dy_percent
			ymax += sign * dy * dy_percent
			self._plot.setYRange(ymin, ymax, padding=0)

	''' Split widget interaction '''

	def on_split_mode_update(self, force_update=False):
		on = self._is_editable and self.store['split_mode']
		if force_update or (self._split_on != on): # Set mouse interaction
			if on:
				# Disable normal mouse interaction and go into split mode
				selected = self.store['selected_units']
				assert len(selected) == 1
				label = list(selected)[0]
				self._splitWidget.show()
				self.addStyle('border: 4px solid red;')
				self._layout.setContentsMargins(4, 4, 4, 4)
				self._plot.setMouseEnabled(x=False, y=False)
				disconnect_if_connected(self._plot.scene().sigMouseMoved, self.mouseMoved)
				disconnect_if_connected(self._scatter.sigClicked, self.mouseClicked)
				QApplication.setOverrideCursor(Qt.CrossCursor)
				self._polygon.setColorIndex(label)
			else:
				self._splitWidget.hide()
				self.clearStyle()
				self._layout.setContentsMargins(2, 2, 2, 2)
				self._plot.setMouseEnabled(x=(self.ndim() == 2), y=True)
				self._plot.scene().sigMouseMoved.connect(self.mouseMoved)
				self._scatter.sigClicked.connect(self.mouseClicked)
				self._divider.setEnabled(False)
				self._polygon.setEnabled(False)
				QApplication.restoreOverrideCursor()
			for sel in self._axSelectors:
				sel.setEnabled(not on)
			self._split_on = on
			self.on_split_nd_update()

	def on_split_nd_update(self):
		self._split_nd = 2 if (self._ndToggle is None or self._ndToggle.isChecked()) else 1
		if self._split_on:
			self._applysplitbtn.setEnabled(False)
			if self._split_nd == 1:
				self._divider.setEnabled(True)
				self._polygon.setEnabled(False)
			else:
				self._divider.setEnabled(False)
				self._polygon.setEnabled(True)

	def on_split_apply(self):
		assert self._split_on
		msg = 'The split operation cannot be undone, and any changes will be saved immediately.'
		if global_settings.gui_tag == 'SLLVMultiBatch' and type(self.store['visible_data']) == LVBatch:
			msg += '\n\nAdditionally, as you are performing a split in the detailed view, you will need to re-summarize your data following this operation to maintain consistency.'
		msg += '\n\nProceed?'
		result = show_warning(msg)
		if result == QtWidgets.QMessageBox.Cancel:
			return
		selected = self.store['selected_units']
		assert len(selected) == 1
		label = list(selected)[0]
		if self._split_nd == 1:
			index = self._divider.getStartIndex(self._xs)
			index += (self._data.labels[index:] == label).argmax() # Advance index to exact label match; this is necessary to retain consistency between summarized and detailed views
			assert self._data.labels[index] == label
			self.store.dispatch(GUIAction(
				tag='split_1d', 
				payload={
					'label': label,
					'start_index': index
				}
			))
		else:
			self.store.dispatch(GUIAction(
				tag='split_2d', 
				payload={
					'label': label, 
					'indices': self._polygon.getContainedIndices(self._xs, self._ys),
				}
			))
		self.store.dispatch(GUIAction(tag='save_edits'))

	def on_split_reset(self):
		assert self._split_on
		if self._split_nd == 1:
			self._divider.setEnabled(True)
		else:
			self._polygon.setEnabled(True)
		self._applysplitbtn.setEnabled(False)
		QApplication.setOverrideCursor(Qt.CrossCursor)

	def on_split_complete(self):
		print('Split completed')
		self._applysplitbtn.setEnabled(True)
		QApplication.restoreOverrideCursor()

	''' Mouse interaction '''

	def mouseMoved(self, pos):
		pass

	def mouseHovered(self, plot, points):
		idx = points[0].index() if len(points) > 0 else None
		if idx != self.store['hovered']:
			self.store.dispatch(GUIAction(tag='hover', payload=idx))

	def mouseClicked(self, plot, points):
		if len(points) > 0:
			idx = points[0].index()
			label = self.store['visible_data'].labels[idx]
			self.store.dispatch(GUIAction(tag='select', payload=label))