'''
Base abstract widget for MultiBatch data
'''
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QShortcut
from qtpy.QtGui import QKeySequence
import pyqtgraph as pg
import math

from ephys2.gui.utils import *
from ephys2.gui.embed.selector import *
from ephys2.gui.sidebar import *
from ephys2.lib.singletons import global_metadata

from .store import *

class MultiBatchWidget(GUIWidget, QtWidgets.QMainWindow, metaclass=QtABCMeta):
	scale_options: List[str] = ['sec', 'min', 'hour']
	scalemult = {'sec': 1, 'min': 60, 'hour': 3600}

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

		# Render main view
		self._main = EmbedSelectorWidget(self.store)
		self._main.selectEmbedding('Peak amplitude (1D)')
		self._chgroupSelector = pg.ComboBox()
		self._filePathsViewer = pg.ComboBox()
		self._filePathsViewer.addItems(['Loaded files...'])
		self._metadataViewer = pg.ComboBox()
		self._metadataViewer.addItems(['Metadata...'])
		self._summaryText = QtWidgets.QLabel('')
		self._windowEdit0 = QtWidgets.QLineEdit()
		self._windowScale0 = pg.ComboBox()
		self._windowScale0.addItems(self.scale_options)
		self._windowEdit1 = QtWidgets.QLineEdit()
		self._windowScale1 = pg.ComboBox()
		self._windowScale1.addItems(self.scale_options)
		self._collapseGapsEdit = QtWidgets.QLineEdit()
		self._collapseGapsEdit.setText('inf')
		self._saveButton = IconButton('SP_DialogSaveButton', size=(20,20))
		self._saveButton.setToolTip('Save your edits to the HDF5 file.')
		self._saveButton.hide() # Hide until edited

		# Render auxiliary views
		self._sidebar = SidebarWidget()
		self._sidebar['Waveform'] = WaveformWidget(self.store)

		# Declare data embeddings
		self._embeddings = [
			self._main
		]

		# Layout - main
		self._leftWidget = VLayoutWidget()
		self._topWidget = HLayoutWidget()
		self._topWidget._layout.addWidget(QtWidgets.QLabel('Channel group:'))
		self._topWidget._layout.addWidget(self._chgroupSelector)
		self._topWidget._layout.addWidget(self._filePathsViewer)
		self._topWidget._layout.addWidget(self._metadataViewer)
		self._topWidget._layout.addStretch()
		self._leftWidget._layout.addWidget(self._topWidget)
		self._tabs = QtWidgets.QTabWidget()
		self._tabs.addTab(self._main, "Main")
		self._leftWidget._layout.addWidget(self._tabs)
		self._bottomWidget = HLayoutWidget()
		self._leftWidget._layout.addWidget(self._bottomWidget)
		self._bottomWidget._layout.addWidget(self._summaryText)
		self._bottomWidget._layout.addStretch()
		self._bottomWidget._layout.addWidget(QtWidgets.QLabel('Window:'))
		self._bottomWidget._layout.addWidget(self._windowEdit0)
		self._bottomWidget._layout.addWidget(self._windowScale0)
		self._bottomWidget._layout.addWidget(QtWidgets.QLabel('to'))
		self._bottomWidget._layout.addWidget(self._windowEdit1)
		self._bottomWidget._layout.addWidget(self._windowScale1)
		self._bottomWidget._layout.addStretch()
		self._bottomWidget._layout.addWidget(QtWidgets.QLabel('Collapse gaps > '))
		self._bottomWidget._layout.addWidget(self._collapseGapsEdit)
		self._bottomWidget._layout.addWidget(QtWidgets.QLabel('hr'))
		self._bottomWidget._layout.addWidget(self._saveButton)
		splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
		splitter.addWidget(self._leftWidget)
		splitter.addWidget(self._sidebar)
		splitter.setSizes([2500, 1000])
		self.setCentralWidget(splitter)

		# Callbacks
		self.escShortcut = QShortcut(QKeySequence('Esc'), self)
		self.escShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='reset_view', payload=None)))
		self._windowEdit0.returnPressed.connect(self.on_edit_window)
		self._windowScale0.currentIndexChanged.connect(lambda _: self.on_update_window())
		self._windowEdit1.returnPressed.connect(self.on_edit_window)
		self._windowScale1.currentIndexChanged.connect(lambda _: self.on_update_window())
		self._chgroupSelector.currentIndexChanged.connect(lambda _: self.on_set_channel_group())
		self._collapseGapsEdit.returnPressed.connect(self.on_collapse_gaps)
		self._saveButton.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='save_edits', payload=None)))

		self.subscribe_store('data', self.on_update_window)
		self.subscribe_store('item_id', lambda: self._chgroupSelector.setValue(str(self.store['item_id'])))
		self.subscribe_store('items', lambda: self._chgroupSelector.addItems([str(i) for i in self.store['items']]))
		self.subscribe_store('edited', self.on_edited_update)

	''' Public API ''' 

	def set_files(self, filepaths: List[ROFilePath]):
		self.store.dispatch(GUIAction(tag='set_files', payload=filepaths))
		self._filePathsViewer.addItems(filepaths)
		self._metadataViewer.addItems([f'{key}: {value}' for key, value in global_metadata.items()])

	def on_edit_window(self):
		t0 = validate_float(self._windowEdit0.text(), 0, np.inf)
		t1 = validate_float(self._windowEdit1.text(), 0, np.inf)
		if t0 == None or t1 == None:
			return
		if t0 == np.inf:
			show_error('Please enter a value less than infinity for the start time.')
			return
		t0 *= math.floor(global_metadata['sampling_rate'] * self.scalemult[self._windowScale0.currentText()])
		t1 *= math.ceil(global_metadata['sampling_rate'] * self.scalemult[self._windowScale1.currentText()])
		if t0 > t1: 
			show_error('Please enter a start time less than the end time.')
			return
		self.store.dispatch(GUIAction(tag='set_window', payload=(t0, t1)))

	def on_update_window(self):
		# When the window has been updated externally
		ts = self.store['data'].time
		if ts.size > 0:
			t0 = ts[0] / (global_metadata['sampling_rate'] * self.scalemult[self._windowScale0.currentText()])
			t1 = ts[-1] / (global_metadata['sampling_rate'] * self.scalemult[self._windowScale1.currentText()])
			self._windowEdit0.setText(str(round(t0, 2)))
			self._windowEdit1.setText(str(round(t1, 2)))

	def on_set_channel_group(self):
		chgroup = self._chgroupSelector.currentText()
		if chgroup != '':
			chgroup = int(chgroup)
			if chgroup != self.store['item_id']:
				self.store.dispatch(GUIAction(tag='set_chgroup', payload=chgroup))

	def on_collapse_gaps(self):
		val = validate_float(self._collapseGapsEdit.text(), 0, np.inf)
		if val != None:
			if val < np.inf:
				val = int(val * global_metadata['sampling_rate'] * 3600)
			self.store.dispatch(GUIAction(tag='set_max_gap', payload=val))

	def on_edited_update(self):
		if self.store['edited']:
			self._saveButton.show()
		else:
			self._saveButton.hide()