'''
Widget for SBatch data
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QShortcut
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QApplication
import pyqtgraph as pg
import numpy as np

from ephys2.lib.types import *
from ephys2.lib.singletons import global_metadata
from ephys2.gui.types import *
from ephys2.gui.utils import *
from ephys2.gui.sidebar import *
import ephys2.gui.colors as gc

from .store import *

class SBatchWidget(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Initialize store & connect to widgets
		self.store = self._makeStore()
		self._connectStore()

		# Initialize widgets
		self._renderMain()

		# Connect UI actions
		self._connectActions()

	def _makeStore(self):
		return SBatchStore()

	def _connectStore(self):
		self.store.subscribe('data', lambda: self._recv_data())
		self.store.subscribe('color_group', lambda: self._drawPlot())
		self.store.subscribe('threshold', lambda: self._drawPlot())
		self.store.subscribe('signal_height', lambda: self._drawPlot())

	def _renderMain(self):
		self.graphWidget = pg.GraphicsLayoutWidget()
		self.graphWidget.setBackground('w')
		self.graphWidget.ci.layout.setContentsMargins(0, 0, 0, 0)
		self.graphWidget.ci.layout.setSpacing(0)
		self._plot = self.graphWidget.addPlot()
		# plot.getAxis('left').setStyle(showValues=False)
		self._plot.setMouseEnabled(x=False)
		self._plot.getViewBox().suggestPadding = lambda *_: 0
		self._plot.setLabel('bottom', 'Time', units='sample')
		self._vline = pg.InfiniteLine(pos=0, pen='black')
		self._plot.addItem(self._vline)
		self._isDrawn = False
		self._drawPlot()
		self._curves = []
		self._thresholds = []
		self._ptr = 0
		self._w_ptr = 0
		self._timer = None

		self.leftLayout = VLayout()
		self.topLayout = HLayout()
		self.stopButton = IconButton('SP_MediaStop')
		self.playButton = IconButton('SP_MediaPlay')
		self.ffButton = IconButton('SP_MediaSeekForward')
		self.rwButton = IconButton('SP_MediaSeekBackward')
		self.startButton = IconButton('SP_MediaSkipBackward')
		self.endButton = IconButton('SP_MediaSkipForward')
		for btn in [self.startButton, self.rwButton, self.stopButton, self.playButton, self.ffButton, self.endButton]:
			self.topLayout.addWidget(btn)
		self.timeText = QtWidgets.QLabel('')
		self.topLayout.addWidget(self.timeText)

		self.topLayout.addStretch()

		self.topLayout.addWidget(QtWidgets.QLabel('Skip to sample:'))
		self.sampleEdit = QtWidgets.QLineEdit()
		self.sampleEdit.setText('0')
		self.topLayout.addWidget(self.sampleEdit)
		self.topLayout.addWidget(QtWidgets.QLabel('Window size (ms):'))
		self.windowSizeEdit = QtWidgets.QLineEdit()
		self.topLayout.addWidget(self.windowSizeEdit)
		self.topLayout.addWidget(QtWidgets.QLabel('Highpass:'))
		self.highpassEdit = QtWidgets.QLineEdit()
		self.highpassEdit.setText('0')
		self.topLayout.addWidget(self.highpassEdit)
		self.topLayout.addWidget(QtWidgets.QLabel('Lowpass:'))
		self.lowpassEdit = QtWidgets.QLineEdit()
		self.lowpassEdit.setText('inf')
		self.topLayout.addWidget(self.lowpassEdit)

		topWidget = QtWidgets.QWidget()
		topWidget.setLayout(self.topLayout)
		self.leftLayout.addWidget(topWidget)

		self.leftLayout.addWidget(self.graphWidget)
		leftWidget = QtWidgets.QWidget()
		leftWidget.setLayout(self.leftLayout)
		self.bottomLayout = HLayout()
		bottomWidget = QtWidgets.QWidget()
		bottomWidget.setLayout(self.bottomLayout)
		self.leftLayout.addWidget(bottomWidget)
		self.summaryText = QtWidgets.QLabel('')
		self.bottomLayout.addWidget(self.summaryText)

		self.bottomLayout.addStretch()

		self.bottomLayout.addWidget(QtWidgets.QLabel('Color group size:'))
		self.colorGroupEdit = QtWidgets.QLineEdit()
		self.colorGroupEdit.setText(str(self.store['color_group']))
		self.bottomLayout.addWidget(self.colorGroupEdit)
		self.bottomLayout.addWidget(QtWidgets.QLabel('Draw threshold:'))
		self.thresholdEdit = QtWidgets.QLineEdit()
		self.thresholdEdit.setText(str(self.store['threshold']))
		self.bottomLayout.addWidget(self.thresholdEdit)
		self.bottomLayout.addWidget(QtWidgets.QLabel('Signal height:'))
		self.sigHeightEdit = QtWidgets.QLineEdit()
		self.sigHeightEdit.setText(str(self.store['signal_height']))
		self.bottomLayout.addWidget(self.sigHeightEdit)

		self._drawPlot()
		self.setCentralWidget(leftWidget)

	def _drawPlot(self):
		data = self.store['data']
		if not (data is None):
			for curve in self._curves:
				self._plot.removeItem(curve)
			for thresh in self._thresholds:
				self._plot.removeItem(thresh)
			self._curves = []
			self._thresholds = []
			H = self.store['signal_height']
			self._plot.setYRange(0, H * 2 * self.store['window_y'])
			self._plot.getAxis('left').setTicks([[
				((2 * i + 1) * H, f'Channel {i}') for i in range(data.ndim)
			]])
			self._plot.getViewBox().setLimits(yMin=0, yMax=H * 2 * data.ndim)
			for i in range(data.ndim):
				c_i = 0 if self.store['color_group'] == np.inf else (i // self.store['color_group'])
				curve = pg.PlotDataItem(pen=gc.primary_pens[c_i % gc.n_colors], autoDownsample=True, skipFiniteCheck=True)
				self._plot.addItem(curve)
				self._curves.append(curve)
				thr_val = 0 if self.store['threshold'] == np.inf else self.store['threshold']
				threshold1 = pg.InfiniteLine(pos=(thr_val + (2 * i + 1) * H), angle=0, pen=gc.primary_pens[c_i % gc.n_colors])
				threshold2 = pg.InfiniteLine(pos=(-thr_val + (2 * i + 1) * H), angle=0, pen=gc.primary_pens[c_i % gc.n_colors])
				self._plot.addItem(threshold1)
				self._plot.addItem(threshold2)
				self._thresholds.append(threshold1)
				self._thresholds.append(threshold2)
			self.summaryText.setText(f'Sampling rate: {data.fs}; Channels: {data.ndim}')
			self._resetScrub()
			self._isDrawn = True

	def _update_time(self):
		W = self.store['window_x']
		sample = self.store['data'].time[self._w_ptr] 
		t = self._format_time(sample)
		self.timeText.setText(f'Time: {t}  Sample: {sample}')

	def _resetScrub(self):
		self._w_ptr = 0
		data = self.store['data']
		H = self.store['signal_height']
		W_x = self.store['window_x']
		tdata = data.time[:W_x]
		self._vline.setValue(tdata[self._w_ptr])
		for i in range(data.ndim):
			self._curves[i].setData(
				tdata, 
				data.data[:W_x, i] + (2 * i + 1) * H
			)
		self._update_time()

	def _scrub(self):
		''' Advance the plot by one element ''' 
		N_x, W_x, data = self.store['N_x'], self.store['window_x'], self.store['data']
		H = self.store['signal_height']
		S = self.store['speed']
		if self._ptr < N_x:
			self._ptr += S
			if self._w_ptr < W_x - 1:
				self._w_ptr += S
				self._w_ptr = min(self._w_ptr, W_x - 1)
				start1, stop1 = W_x, W_x + self._w_ptr
				start2, stop2 = self._w_ptr, W_x
				tdata = data.time[W_x:]
				self._vline.setValue(tdata[self._w_ptr])
				ddata = np.concatenate((data.data[start1:stop1], data.data[start2:stop2]), axis=0)
				for i in range(data.ndim):
					self._curves[i].setData(
						tdata, 
						ddata[:, i] + (2 * i + 1) * H
					)
				self._update_time()
			else:
				self._scrub_right()
		else:
			print('Reached end of data.')
			self._stop_scrubbing()
		QApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

	def _scrub_right(self):
		self.store.dispatch(GUIAction(tag='right', payload=None))
		self._resetScrub()

	def _scrub_left(self):
		self.store.dispatch(GUIAction(tag='left', payload=None))
		self._resetScrub()

	def _zoom_in(self):
		self.store.dispatch(GUIAction(tag='zoom_in', payload=None))
		self._resetScrub()

	def _zoom_out(self):
		self.store.dispatch(GUIAction(tag='zoom_out', payload=None))
		self._resetScrub()

	def _start_scrubbing(self):
		if self._timer is None:
			self._timer = QtCore.QTimer()
			self._timer.timeout.connect(self._scrub)
			self._timer.start(16) # Update at 60 fps

	def _stop_scrubbing(self):
		if not (self._timer is None):
			self._timer.stop()
			self._timer = None

	def _ff(self):
		self.store['speed'] = self.store['speed'] * 2

	def _rw(self):
		self.store['speed'] = int(min(1, self.store['speed'] // 2))

	def _format_time(self, sample: int):
		ms = 1000 * sample / global_metadata['sampling_rate']
		h, r = np.divmod(ms, 3600000)
		m, r = np.divmod(r, 60000)
		s = round(r / 1000, 3)
		return f'{int(h)}:{int(m)}:{s}'

	def _recv_data(self):
		data = self.store['data']
		self._ptr = data.size
		N = min(data.size, self.store['window_x'])
		self.windowSizeEdit.setText(str(int(1000 * N / data.fs)))
		if self._isDrawn and self._timer is None:
			self._resetScrub()

	def _skip_to_sample(self, sample: int):
		self._stop_scrubbing()
		self.store.dispatch(GUIAction(tag='skip_to', payload=sample))

	def _connectActions(self):
		self.rShortcut = QShortcut(QKeySequence('Right'), self)
		self.rShortcut.activated.connect(lambda: self._scrub_right())
		self.lShortcut = QShortcut(QKeySequence('Left'), self)
		self.lShortcut.activated.connect(lambda: self._scrub_left())
		self.ziShortcut = QShortcut(QKeySequence('Ctrl+='), self)
		self.ziShortcut.activated.connect(lambda: self._zoom_in())
		self.zoShortcut = QShortcut(QKeySequence('Ctrl+-'), self)
		self.zoShortcut.activated.connect(lambda: self._zoom_out())

		self.playButton.clicked.connect(lambda: self._start_scrubbing())
		self.stopButton.clicked.connect(lambda: self._stop_scrubbing())
		self.ffButton.clicked.connect(lambda: self._ff())
		self.rwButton.clicked.connect(lambda: self._rw())
		self.startButton.clicked.connect(lambda: self._skip_to_sample(0))
		self.endButton.clicked.connect(lambda: self._skip_to_sample(np.inf))

		self.highpassEdit.returnPressed.connect(lambda: self.store.dispatch(GUIAction(tag='set_highpass', payload=validate_int(self.highpassEdit.text(), 0, np.inf))))
		self.lowpassEdit.returnPressed.connect(lambda: self.store.dispatch(GUIAction(tag='set_lowpass', payload=validate_int(self.lowpassEdit.text(), 0, np.inf))))
		self.sampleEdit.returnPressed.connect(lambda: self._skip_to_sample(validate_int(self.sampleEdit.text(), 0, np.inf)))
		self.windowSizeEdit.returnPressed.connect(lambda: self.store.dispatch(
			GUIAction(tag='set_window', payload=validate_int(self.windowSizeEdit.text(), 0, np.inf) * int(global_metadata['sampling_rate'] / 1000)))
		)
		self.colorGroupEdit.returnPressed.connect(lambda: self.store.dispatch(GUIAction(tag='set_color_group', payload=validate_int(self.colorGroupEdit.text(), 0, np.inf))))
		self.thresholdEdit.returnPressed.connect(lambda: self.store.dispatch(GUIAction(tag='set_threshold', payload=validate_int(self.thresholdEdit.text(), 0, np.inf))))
		self.sigHeightEdit.returnPressed.connect(lambda: self.store.dispatch(GUIAction(tag='set_signal_height', payload=validate_int(self.sigHeightEdit.text(), 0, np.inf))))

	def set_files(self, filepaths: List[ROFilePath]):
		assert len(filepaths) == 1
		self.store.dispatch(GUIAction(tag='set_file', payload=filepaths[0]))
		self._drawPlot()
