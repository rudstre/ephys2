'''
Widget for LLVBatch data
'''
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import os
import colorcet as cc
import pdb
import numpy as np

from ephys2.lib.types import *
from ephys2.gui.types import *
from ephys2.gui.utils import *
from ephys2.gui.sidebar import *
from ephys2.gui.lvbatch.widget import *

from .store import *

class LLVMultiBatchWidget(LVMultiBatchWidget):

	def __init__(self, store: GUIStore, *args, **kwargs):
		LVMultiBatchWidget.__init__(self, store, *args, **kwargs)

		# Callbacks
		self.subscribe_store('split_mode', self.on_split_mode_update)

	def on_split_mode_update(self):
		on = self.store['split_mode']
		self._topWidget.setEnabled(not on)
		self._bottomWidget.setEnabled(not on)
		self._saveButton.setEnabled(not on)