'''
Widget for LTBatch data
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QShortcut
from qtpy.QtGui import QKeySequence
import pyqtgraph as pg

from ephys2.lib.types import *
from ephys2.lib.array import *
from ephys2.gui.types import *
from ephys2.gui.utils import *
from ephys2.gui.sidebar import *
from ephys2.gui.tbatch.widget import *
import ephys2.gui.colors as gc

from .store import *

class LTMultiBatchWidget(TMultiBatchWidget):

	def _connectStore(self):
		self.store = LTMultiBatchStore()
		self.store.subscribe('data', lambda: self._redrawRaster())

	def _redrawData(self):
		data = self.store['data']
		if not (data is None):
			for i, (item_id, item) in enumerate(data.items.items()):
				labels = aggregate_labels(item.labels)
				self._plots[i].setLabel('left', item_id)
				self._plots[i].setXRange(self.store['range'][0], self.store['range'][1])
				self._plots[i].setYRange(min_def(labels, 0)-0.5, max_def(labels, 0)+0.5)
				self._ticks[i].setData(
					item.time,
					labels,
					pen = gc.primary_pens[labels % gc.n_colors]
				)

def aggregate_labels(labels):
	'''
	Convert labels down to a 0-N range.
	'''
	labels_ = labels.copy()
	for i, lb in enumerate(np.unique(labels)):
		labels_[labels == lb] = i
	return labels_
