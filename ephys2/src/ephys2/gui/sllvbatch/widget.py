'''
SLLVBatch viewer combining LLVBatch and SLVBatch views
'''
from qtpy import QtCore, QtGui, QtWidgets

from ephys2.gui.types import *
from ephys2.gui.llvbatch.widget import *
from .store import *

class SLLVMultiBatchWidget(GUIWidget, QtWidgets.QMainWindow):

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
		self._summaryView = SLVMultiBatchWidget(self.store)
		self._detailView = LLVMultiBatchWidget(self.store.detail_store)
		self._tabs = QtWidgets.QTabWidget()
		self._tabs.addTab(self._summaryView, 'Summary')
		self._tabs.addTab(self._detailView, 'Detail')
		self.setCentralWidget(self._tabs)

		# Listeners
		self.subscribe_store('view_mode', self.on_view_mode_update)

	def set_files(self, filepaths: List[ROFilePath]):
		self._summaryView.set_files(filepaths)
		self._detailView.set_files(filepaths)

	def on_view_mode_update(self):
		current_mode = ['summary', 'detail'][self._tabs.currentIndex()]
		if current_mode != self.store['view_mode']:
			self._tabs.setCurrentIndex((self._tabs.currentIndex() + 1) % 2)

class SLVMultiBatchWidget(LLVMultiBatchWidget):

	def __init__(self, store: GUIStore, *args, **kwargs):
		super().__init__(store, *args, **kwargs)
		# Disable cross-correlation and firing rates for now
		del self._sidebar['Cross-correlation']
		# del self._sidebar['Firing rate']