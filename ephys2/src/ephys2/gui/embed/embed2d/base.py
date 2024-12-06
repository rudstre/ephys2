'''
Widget for embedding & selecting scatter data in 2-dimensional embeddings.
'''

from typing import Dict, Tuple, Optional
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import QPointF
from qtpy.QtWidgets import QShortcut
from qtpy.QtGui import QKeySequence
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
from abc import ABC, abstractmethod
from scipy.stats import gaussian_kde

from ephys2.gui.embed.base import *
from ephys2.lib.cluster import *

class Embed2dWidget(EmbedWidget):
	'''
	Embed the data in 2 dimensions with optional density estimation.
	'''
	n_kde_contours = 10
	n_kde_points = 100

	@staticmethod
	def ndim() -> int:
		return 2

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Density rendering
		# self._enableDensityBox = QtWidgets.QCheckBox('Density')
		# self._hLayout.addWidget(self._enableDensityBox)
		self._contours = [
			pg.IsocurveItem(pen='r') for _ in range(self.n_kde_contours)
		]
		vb = self._scatter.getViewBox()
		for c in self._contours:
			vb.addItem(c)
		# self._enableDensityBox.setChecked(False)
		# self._enableDensityBox.toggled.connect(self._toggleDensity)

		# Navigational shortcuts
		self.uShortcut = QShortcut(QKeySequence('Up'), self)
		self.uShortcut.activated.connect(lambda: self.translate_view(0, self.step_percent))
		self.dShortcut = QShortcut(QKeySequence('Down'), self)
		self.dShortcut.activated.connect(lambda: self.translate_view(0, -self.step_percent))
		self.rShortcut = QShortcut(QKeySequence('Right'), self)
		self.rShortcut.activated.connect(lambda: self.translate_view(self.step_percent, 0))
		self.lShortcut = QShortcut(QKeySequence('Left'), self)
		self.lShortcut.activated.connect(lambda: self.translate_view(-self.step_percent, 0))
		self.ziShortcut = QShortcut(QKeySequence('Ctrl+='), self)
		self.ziShortcut.activated.connect(lambda: self.zoom_view(self.step_percent, self.step_percent))
		self.zoShortcut = QShortcut(QKeySequence('Ctrl+-'), self)
		self.zoShortcut.activated.connect(lambda: self.zoom_view(-self.step_percent, -self.step_percent))

	def _updatePlot(self):
		super()._updatePlot()
		# Update density contours
		# if self._enableDensityBox.isChecked():
		# 	self._updateDensity()

	def _updateDensity(self):
		if not (self._xs is None) and self._xs.size > 0:
			xmin, xmax = self._plot.getAxis('bottom').range
			ymin, ymax = self._plot.getAxis('left').range
			density = gaussian_kde(np.vstack((self._xs, self._ys)))
			xgrid, ygrid = np.mgrid[xmin:xmax:self.n_kde_points*1j, ymin:ymax:self.n_kde_points*1j]
			xygrid = np.vstack([xgrid.ravel(), ygrid.ravel()])
			Z = np.reshape(density(xygrid).T, xgrid.shape)
			zlevels = np.linspace(Z.min(), Z.max(), self.n_kde_contours)
			tr = QtGui.QTransform.fromScale(
				(xmax - xmin) / self.n_kde_points, 
				(ymax - ymin) / self.n_kde_points
			)
			for i, z in enumerate(zlevels):
				self._contours[i].setData(Z, level=z)
				self._contours[i].setPos(xmin, ymin)
				self._contours[i].setTransform(tr, combine=False)

	def _toggleDensity(self):
		if self._enableDensityBox.isChecked():
			self._updateDensity()
			for c in self._contours:
				c.show()
		else:
			for c in self._contours:
				c.hide()

