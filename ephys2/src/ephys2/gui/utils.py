'''
Utilities for ephys2 QT GUI
'''
from typing import Tuple
from qtpy import QtCore, QtGui, QtWidgets 
from qtpy.QtCore import Qt
from collections import defaultdict
import numpy as np
import numpy.typing as npt
import abc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as MplFigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as MplNavigationToolbar
from matplotlib.figure import Figure
import shortuuid

from ephys2.lib.types import *

def show_error(msg_str: str):
	msg = QtWidgets.QMessageBox()
	msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
	msg.setText("Error")
	msg.setInformativeText(msg_str)
	msg.setWindowTitle("Error")
	return msg.exec()

def show_warning(msg_str: str):
	msg = QtWidgets.QMessageBox()
	msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
	msg.setText("Warning")
	msg.setInformativeText(msg_str)
	msg.setWindowTitle("Warning")
	msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
	return msg.exec()

def get_peak_amp(data: npt.NDArray[np.float32], channel: int=0, n_channels: int=4) -> npt.NDArray[np.float32]:
	'''
	Convert an N x M dataset to N x 1 by reducing to peak amplitude.
	'''
	N = data.shape[0]
	M = data.shape[1] // n_channels
	chan = data[:, channel*M:(channel + 1)*M]
	y = chan[np.arange(N), np.abs(chan).argmax(axis=1)]
	assert y.shape[0] == data.shape[0]
	return y

def HSpacer() -> QtWidgets.QWidget:
	'''
	Dynamically resizing horizontal spacer.
	'''
	spacer = QtWidgets.QWidget()
	spacer.setSizePolicy(
		QtWidgets.QSizePolicy.Policy.Expanding,
		QtWidgets.QSizePolicy.Policy.Minimum
	)
	return spacer

def IconAction(parent, name: str, callback) -> QtWidgets.QAction:
	'''
	Construct icon button from standard system library.
	'''
	icon = QtWidgets.QApplication.style().standardIcon(
		getattr(QtWidgets.QStyle.StandardPixmap, name)
	)
	action = QtWidgets.QAction(icon, name, parent)
	action.triggered.connect(callback)
	return action

def IconButton(name: str, size: Tuple[int, int]=(16, 16)) -> QtWidgets.QPushButton:
	button = QtWidgets.QPushButton()
	icon = QtWidgets.QApplication.style().standardIcon(
		getattr(QtWidgets.QStyle.StandardPixmap, name)
	)
	button.setIcon(icon)
	button.setIconSize(QtCore.QSize(*size))
	return button

def ProxyWrap(widget: QtWidgets.QWidget):
	'''
	Wrap a widget in a proxy; primarily used for adding widgets
	to pyqtgraph.GraphicsLayoutWidget.
	'''
	proxy = QtWidgets.QGraphicsProxyWidget()
	proxy.setWidget(widget)
	return proxy

class QtABCMeta(type(QtCore.QObject), abc.ABCMeta):
	pass

class VScrollArea(QtWidgets.QScrollArea):
	'''
	Utility class for scroll area with common options
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setWidgetResizable(True)
		self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		widget = VLayoutWidget()
		self._layout = widget._layout
		self.setWidget(widget)

class HScrollArea(QtWidgets.QScrollArea):
	'''
	Utility class for scroll area with common options
	'''
	def __init__(self, *args, vmargin: int=0, **kwargs):
		super().__init__(*args, **kwargs)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setWidgetResizable(True)
		self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		self._vmargin = vmargin
		widget = HLayoutWidget()
		self._layout = widget._layout
		self.setWidget(widget)
		self.setSizePolicy(QtWidgets.QSizePolicy(
			QtWidgets.QSizePolicy.Policy.Preferred,
			QtWidgets.QSizePolicy.Policy.Fixed
		))

	def sizeHint(self):
		w, h = 0, 0
		for widget in layout_widgets(self._layout):
			w += widget.sizeHint().width()
			h = max(h, widget.sizeHint().height())
		return QtCore.QSize(w, h + self._vmargin)

class MatplotlibWidget(QtWidgets.QWidget):
	'''
	Rendering matplotlib graphs as widgets
	'''
	def __init__(self, *args, fig=Figure(), size=(300,300), **kwargs):
		super().__init__(*args, **kwargs)
		self._layout = VLayout()
		self.setLayout(self._layout)
		self._size = size
		self.setSizePolicy(QtWidgets.QSizePolicy(
			QtWidgets.QSizePolicy.Policy.Fixed,
			QtWidgets.QSizePolicy.Policy.Fixed
		))
		self.setFigure(fig)

	def draw(self):
		self._canvas.draw()

	def setFigure(self, fig: Figure):
		clear_layout(self._layout)
		fig.set_tight_layout(dict(pad=0, w_pad=0, h_pad=0))
		self._fig = fig
		self._canvas = MplFigureCanvas(self._fig)
		self._canvas.setParent(self)
		self._canvas.wheelEvent = lambda evt: evt.ignore() # Pass scroll to parent
		# self._toolbar = MplNavigationToolbar(self._canvas, self)
		# self._layout.addWidget(self._toolbar)
		self._layout.addWidget(self._canvas)
		self.draw()

	def sizeHint(self) -> QtCore.QSize:
		return QtCore.QSize(*self._size)

	def wheelEvent(self, evt):
		# Pass scroll to parent
		evt.ignore() 

def validate_int(text: str, low: float=-np.inf, high: float=np.inf):
	'''
	Validate text as int between range
	'''
	try:
		if low == -np.inf and text == '-inf':
			return -np.inf
		elif high == np.inf and text == 'inf':
			return np.inf
		else:
			val = int(text)
			assert low <= val
			assert val <= high
			return val
	except:
		show_error(f'Please enter an integer in the range [{low}, {high}]')

def validate_float(text: str, low: float=-np.inf, high: float=np.inf):
	'''
	Validate text as int between range
	'''
	try:
		if low == -np.inf and text == '-inf':
			return -np.inf
		elif high == np.inf and text == 'inf':
			return np.inf
		else:
			val = float(text)
			assert low <= val
			assert val <= high
			return val
	except:
		show_error(f'Please enter a float in the range [{low}, {high}]')

class HLayout(QtWidgets.QHBoxLayout):
	'''
	HBoxLayout with small margins
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setContentsMargins(2, 2, 2, 2)
		self.setAlignment(Qt.AlignmentFlag.AlignLeft)

class VLayout(QtWidgets.QVBoxLayout):
	'''
	VBoxLayout with small margins
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setContentsMargins(2, 2, 2, 2)
		self.setAlignment(Qt.AlignmentFlag.AlignTop)

class StyledWidget(QtWidgets.QWidget):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._stylename = None

	def addStyle(self, style: str):
		# Lazily add style parameters
		if self._stylename is None:
			self._stylename = shortuuid.uuid()
			self.setAttribute(Qt.WA_StyledBackground)
			self.setObjectName(self._stylename)
		self.setStyleSheet(f'#{self._stylename} {{{style}}}')

	def clearStyle(self):
		self.setStyleSheet('')

class HLayoutWidget(StyledWidget):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._layout = HLayout()
		self.setLayout(self._layout)

	def clearLayout(self):
		clear_layout(self._layout)

class VLayoutWidget(StyledWidget):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._layout = VLayout()
		self.setLayout(self._layout)

	def clearLayout(self):
		clear_layout(self._layout)

class PushButton(QtWidgets.QPushButton):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setStyleSheet('background-color: #DCDCDC')

def get_timescale(nsamples: int, fs: int) -> Tuple[str, float]:
	'''
	Return a timescale and scaling factor based on the number of samples at a 
	particular sampling rate (fs)s
	'''
	scale = 1 / fs
	units = 'seconds'

	dt = nsamples * scale
	if dt > 60:
		dt /= 60 
		scale /= 60
		units = 'minutes'
	if dt > 60:
		dt /= 60
		scale /= 60
		units = 'hours'

	return units, scale

def clear_layout(layout: QtWidgets.QBoxLayout):
	'''
	Clear all widgets from a layout
	'''
	while layout.count():
		child = layout.takeAt(0)
		if child.widget():
			child.widget().deleteLater()

def layout_widgets(layout: QtWidgets.QBoxLayout):
	'''
	Iterate over widgets in a layout
	'''
	return (layout.itemAt(i).widget() for i in range(layout.count()))

class H3Label(QtWidgets.QLabel):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setSizePolicy(QtWidgets.QSizePolicy(
			QtWidgets.QSizePolicy.Policy.Preferred,
			QtWidgets.QSizePolicy.Policy.Fixed
		))

	def sizeHint(self) -> QtCore.QSize:
		return QtCore.QSize(0, 16)

def collapse_time_gaps(times: npt.NDArray[np.int64], max_dt: int, min_gap: int) -> VBatch:
	if times.size > 0 and max_dt < np.inf:
		assert min_gap >= 0
		dt = np.diff(times)
		dt[dt > max_dt] = min_gap
		dt = np.insert(dt, 0, times[0])
		times = np.cumsum(dt)
	return times

def is_shift_pressed() -> bool:
	'''
	Whether Shift is one of the modifier keys currently pressed
	'''
	modifiers = QtWidgets.QApplication.keyboardModifiers()
	return (modifiers & Qt.ShiftModifier) == Qt.ShiftModifier

def resize_to_active_screen(widget: QtWidgets.QWidget):
	'''
	Move and resize the widget to the active screen size
	'''
	screen = get_active_screen()
	widget.move(screen.geometry().center())
	widget.resize(screen.size())

def get_active_screen() -> QtGui.QScreen:
	'''
	Return the active screen
	'''
	return QtWidgets.QApplication.primaryScreen()

def disconnect_if_connected(signal: QtCore.QMetaObject.Connection, slot: Callable):
	'''
	Disconnect a signal if it is connected
	'''
	try:
		signal.disconnect(slot)
	except:
		pass

def remove_item_if_exists(scene: QtWidgets.QGraphicsScene, item: QtWidgets.QGraphicsItem):
	'''
	Remove an item from a scene if it exists
	'''
	try:
		scene.removeItem(item)
	except:
		pass

class WhiteLabel(QtWidgets.QLabel):
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setStyleSheet('background-color: transparent; color: white;')