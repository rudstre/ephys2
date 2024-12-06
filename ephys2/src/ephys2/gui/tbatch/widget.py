'''
Widget for TBatch data
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
import ephys2.gui.colors as gc

from .store import *

class TMultiBatchWidget(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Initialize store & connect to widgets
		self._connectStore()

		# Initialize widgets
		self._renderMain()

		# Connect UI actions
		self._connectActions()

	def _connectStore(self):
		self.store = TMultiBatchStore()
		self.store.subscribe('data', lambda: self._redrawRaster())

	def _renderMain(self):
		self.graphWidget = pg.GraphicsLayoutWidget()
		self.graphWidget.setBackground('w')
		self.graphWidget.ci.layout.setContentsMargins(0, 0, 0, 0)
		self.graphWidget.ci.layout.setSpacing(0)
		self._ticks = []
		self._plots = []
		self._vtick = QtGui.QPainterPath()
		self._vtick.moveTo(0, -0.5)
		self._vtick.lineTo(0, 0.5)

		self.leftLayout = VLayout()
		self.leftLayout.addWidget(self.graphWidget)
		leftWidget = QtWidgets.QWidget()
		leftWidget.setLayout(self.leftLayout)
		self.bottomLayout = HLayout()
		bottomWidget = QtWidgets.QWidget()
		bottomWidget.setLayout(self.bottomLayout)
		self.leftLayout.addWidget(bottomWidget)

		self.minusButton = IconButton('SP_ArrowLeft')
		self.plusButton = IconButton('SP_ArrowRight')
		self.bottomLayout.addWidget(QtWidgets.QLabel(' Showing ', self))
		self.bottomLayout.addWidget(self.minusButton)
		self.nChansText = QtWidgets.QLabel('')
		self.bottomLayout.addWidget(self.nChansText)
		self.bottomLayout.addWidget(self.plusButton)
		self.bottomLayout.addWidget(QtWidgets.QLabel(' streams', self))

		self._redrawRaster()
		self.setCentralWidget(leftWidget)

	def _redrawRaster(self):
		Np = len(self._plots)
		while Np > self.store['window_y']:
			self.graphWidget.removeItem(self._plots[-1])
			del self._plots[-1]
			del self._ticks[-1]
			Np -= 1
		while Np < self.store['window_y']:
			plot = self.graphWidget.addPlot(row=Np, col=0)
			plot.getAxis('left').setStyle(showValues=False)
			plot.setMouseEnabled(x=False, y=False)
			plot.setYRange(-0.5, 0.5)
			if Np > 0:
				self._plots[Np - 1].getAxis('bottom').setStyle(showValues=False)
				self._plots[Np - 1].showLabel('bottom', False)
			if Np == self.store['window_y']-1:
				plot.setLabel('bottom', 'Time', units='sample')
			# plot.getViewBox().suggestPadding = lambda *_: 0
			scatter = pg.ScatterPlotItem(pxMode=False, symbol=self._vtick, size=1, pen='black')
			plot.addItem(scatter)
			self._plots.append(plot)
			self._ticks.append(scatter)
			Np += 1

		self.nChansText.setText(str(self.store['window_y']))
		self._redrawData()

	def _redrawData(self):
		data = self.store['data']
		if not (data is None):
			t0, t1 = self.store['range'][0], self.store['range'][1]
			for i, (item_id, item) in enumerate(data.items.items()):
				self._plots[i].setLabel('left', item_id)
				self._plots[i].setXRange(t0, t1)
				self._ticks[i].setData(x=item.time, y=np.zeros_like(item.time))
			dt = t1 - t0
			units, scale = get_timescale(max(t0, dt), global_metadata['sampling_rate'])
			self._plots[-1].getAxis('bottom').setScale(scale)
			self._plots[-1].setLabel('bottom', 'Time', units=units)

	def _connectActions(self):
		self.uShortcut = QShortcut(QKeySequence('Up'), self)
		self.uShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='up', payload=None)))
		self.dShortcut = QShortcut(QKeySequence('Down'), self)
		self.dShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='down', payload=None)))
		self.rShortcut = QShortcut(QKeySequence('Right'), self)
		self.rShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='right', payload=None)))
		self.lShortcut = QShortcut(QKeySequence('Left'), self)
		self.lShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='left', payload=None)))
		self.ziShortcut = QShortcut(QKeySequence('Ctrl+='), self)
		self.ziShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='zoom_in', payload=None)))
		self.zoShortcut = QShortcut(QKeySequence('Ctrl+-'), self)
		self.zoShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='zoom_out', payload=None)))
		self.minusButton.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='decrease_nchans', payload=None)))
		self.plusButton.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='increase_nchans', payload=None)))

	def set_files(self, filepaths: List[ROFilePath]):
		assert len(filepaths) == 1
		self.store.dispatch(GUIAction(tag='set_file', payload=filepaths[0]))
