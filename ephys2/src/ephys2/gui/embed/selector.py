'''
Selector for possible 1d/2d embeddings
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt, QPointF
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt

from ephys2.lib.settings import global_settings
from ephys2.lib.types import *
from ephys2.gui.utils import *
from ephys2.gui.types import *

from .embed1d.amp1 import *
from .embed1d.pca1 import *
from .embed1d.energy import *
from .embed1d.wpca1 import *
from .embed1d.bwpca1 import *
from .embed2d.amp2 import *
from .embed2d.pca2 import *
from .embed2d.dmd import *
from .embed2d.wpca2 import *
from .embed2d.bwpca2 import *
# from .embed2d.swpca2 import *
# from .embed2d.umap import *
# from .embed2d.tsne2 import *

class EmbedSelectorWidget(GUIWidget, QtWidgets.QWidget):

	@staticmethod
	def selectorMap() -> Dict[str, type]:
		'''
		All must be subclasses of EmbedWidget
		'''
		return {
			'Peak amplitude (1D)': (0, Amp1Widget),
			'PCA (1D)': (1, PCA1Widget),
			'Energy (1D)': (2, EnergyWidget),
			'DWT PCA (1D)': (3, WPCA1Widget),
			'β-weighted DWT PCA (1D)': (4, BWPCA1Widget),
			'Peak amplitude (2D)': (5, Amp2Widget),
			'PCA (2D)': (6, PCA2Widget),
			# 'DMD (2D)': (7, DMDWidget),
			'DWT PCA (2D)': (7, WPCA2Widget),
			'β-weighted DWT PCA (2D)': (8, BWPCA2Widget),
			# 'SWT PCA (2D)': (8, SWPCA2Widget),
			# 'UMAP (2D)': (8, UMAPWidget),
			# 't-SNE (2D)': (9, TSNE2Widget),
		}

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		QtWidgets.QWidget.__init__(self, *args, **kwargs)

		options = list(self.selectorMap().keys())

		# Create selector
		self._selector = pg.ComboBox()
		self._selector.addItems(options)
		self._selector.setCurrentIndex(0)
		self._selector.currentIndexChanged.connect(lambda _: self._updateEmbedding())

		# Create layout
		self._vLayout = VLayout()
		self._vLayout.addWidget(self._selector)
		self.setLayout(self._vLayout)

		# Create child
		self._child = None
		self._updateEmbedding()

		# Split mode
		self._is_editable = global_settings.gui_tag in ['LLVMultiBatch', 'SLLVMultiBatch']	
		if self._is_editable:
			self.subscribe_store('split_mode', self.on_split_mode_update)

	def _updateEmbedding(self):
		idx, Widget = self.selectorMap()[self._selector.currentText()]
		if not (self._child is None):
			self._vLayout.removeWidget(self._child)
			self._child.deleteLater()
		self._child = Widget(self.store)
		self._vLayout.addWidget(self._child)
		if not (self.store['visible_data'] is None):
			self._child.updateData()

	''' Public API '''

	def selectEmbedding(self, sel: str):
		idx, _ = self.selectorMap()[sel]
		self._selector.setCurrentIndex(idx)

	def on_split_mode_update(self):
		on = self.store['split_mode']
		self._selector.setEnabled(not on)