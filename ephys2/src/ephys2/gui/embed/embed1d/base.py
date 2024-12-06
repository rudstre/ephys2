'''
Base 1-dimensional embedding widget (with time as the x-axis)
'''

from typing import Dict, Tuple, Optional
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import QPointF
from qtpy.QtWidgets import QApplication
from qtpy.QtWidgets import QShortcut
from qtpy.QtGui import QKeySequence
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt
import pdb
import math

from ephys2.gui.embed.base import *
from ephys2.gui.utils import *
from ephys2.lib.singletons import global_metadata
from ephys2.lib.settings import global_settings
from ephys2.gui.types import * 

class Embed1dWidget(EmbedWidget):
	'''
	Embed the data in 1 dimension
	'''
	ax_x_padding = 0 # No padding in time axis
	
	@staticmethod
	def ndim() -> int:
		return 1

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._plot.getAxis('bottom').enableAutoSIPrefix(False)

		# Click-drag select
		self._sel_region = pg.LinearRegionItem(orientation='vertical', movable=False)
		self._plot.addItem(self._sel_region)
		self._sel_region.hide()
		self._is_selecting = False
		self._sel_x1 = None
		self._sel_pos1 = None
		self._sel_x2 = None
		self._sel_pos2 = None
		self._mouse_pos = None

		# Jump to detailed time
		if global_settings.gui_tag == 'SLLVMultiBatch':
			self._jumpToAction = self._plot.getViewBox().menu.addAction('Jump to detailed time')
			self._jumpToAction.triggered.connect(self.onJumpTo)

		# Navigational shortcuts
		self.uShortcut = QShortcut(QKeySequence('Up'), self)
		self.uShortcut.activated.connect(lambda: self.translate_view(0, self.step_percent))
		self.dShortcut = QShortcut(QKeySequence('Down'), self)
		self.dShortcut.activated.connect(lambda: self.translate_view(0, -self.step_percent))
		self.rShortcut = QShortcut(QKeySequence('Right'), self)
		self.rShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='right', payload=None)))
		self.lShortcut = QShortcut(QKeySequence('Left'), self)
		self.lShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='left', payload=None)))
		self.ziShortcut = QShortcut(QKeySequence('Ctrl+='), self)
		self.ziShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='zoom_in', payload=None)))
		self.zoShortcut = QShortcut(QKeySequence('Ctrl+-'), self)
		self.zoShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='zoom_out', payload=None)))

	def updateData(self):
		# Compute X axis label per sampling rate
		data = self.store['visible_data']
		if data.size > 2:
			dt = data.time[-1] - data.time[0]
			t0 = data.time[0]  
			units, scale = get_timescale(max(t0, dt), global_metadata['sampling_rate'])
		else:
			units, scale = get_timescale(0, global_metadata['sampling_rate'])
		self._plot.getAxis('bottom').setScale(scale)
		self._plot.setLabel('bottom', 'Time', units=units)
		super().updateData()

	def mouseMoved(self, pos):
		self._mouse_pos = pos
		evts = self._plot.vb.scene().clickEvents
		if len(evts) == 1 and evts[0].button() == Qt.LeftButton:
			if self._is_selecting:
				self._sel_pos2 = pos
				dx = abs(self._sel_pos2.x() - self._sel_pos1.x())
				dy = abs(self._sel_pos2.y() - self._sel_pos1.y())
				if dx > dy and dx > QApplication.startDragDistance():
					self._sel_x2 = self._plot.vb.mapSceneToView(pos).x()
					self._sel_region.setRegion((self._sel_x1, self._sel_x2))
					self._sel_region.show()
				else:
					self._sel_region.hide()
			else:
				self._is_selecting = True
				self._sel_pos1 = pos
				self._sel_x1 = self._plot.vb.mapSceneToView(pos).x()
		elif self._is_selecting:
			if self._sel_region.isVisible():
				self._sel_region.hide()
				x1, x2 = int(self._sel_x1), int(self._sel_x2)
				x1, x2 = min(x1, x2), max(x1, x2)
				self.store.dispatch(GUIAction(tag='select_between', payload=(x1, x2)))
			self._is_selecting = False

	def onJumpTo(self):
		assert self._mouse_pos != None
		x = math.floor(self._plot.vb.mapSceneToView(self._mouse_pos).x())
		self.store.dispatch(GUIAction(tag='jump_to_detail', payload=x))