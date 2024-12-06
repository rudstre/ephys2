'''
Sidebar for rendering auxiliary information.
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt

from ephys2.gui.utils import *

class SidebarWidget(VScrollArea):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._widget_idx: Dict[str, int] = dict()
		self._widget_map: Dict[str, QtWidgets.QWidget] = dict()

	def __contains__(self, name: str):
		return name in self._widget_idx

	def __setitem__(self, name: str, widget: QtWidgets.QWidget):
		'''
		Adds a widget to be displayed as a separate element in the sidebar.
		If already exists, inserts it at the prior position.
		'''
		idx = self._layout.count()
		if name in self._widget_idx:
			idx = self._widget_idx[name]
			self.__delitem__(name)
		self.insertAt(idx, name, widget)

	def __getitem__(self, name: str) -> QtWidgets.QWidget:
		'''
		Get a widget from the sidebar.
		'''
		return self._layout.itemAt(self._widget_idx[name]).widget()._child

	def __delitem__(self, name: str):
		'''
		Delete a widget from the sidebar.
		'''
		idx = self._widget_idx[name]
		wdg = self._widget_map[name]
		item = self._layout.itemAt(idx)
		self._layout.removeItem(item)
		item.widget().deleteLater()
		wdg.deleteLater()
		del self._widget_idx[name]
		del self._widget_map[name]
		for k in self._widget_idx:
			if self._widget_idx[k] > idx:
				self._widget_idx[k] -= 1

	def insertAt(self, idx: int, name: str, widget: QtWidgets.QWidget):
		'''
		Insert a widget at an index
		'''
		idx = min(idx, len(self._widget_idx))
		window = ViewWindow(name, widget)
		window._onClose = lambda: self.__delitem__(name)
		self._layout.insertWidget(idx, window, stretch=0)
		# Check if idx already exists, and increment if so
		if idx in self._widget_idx.values():
			for k, v in self._widget_idx.items():
				if v >= idx:
					self._widget_idx[k] += 1
		self._widget_idx[name] = idx
		self._widget_map[name] = widget

class ViewWindow(QtWidgets.QMainWindow):
	'''
	Base widget for viewing auxiliary info.
	'''
	default_width: int = 500
	default_height: int = 500

	def __init__(self, title: str, child: QtWidgets.QWidget):
		super().__init__()
		self.setSizePolicy(QtWidgets.QSizePolicy(
			QtWidgets.QSizePolicy.Policy.Preferred,
			QtWidgets.QSizePolicy.Policy.Fixed
		))
		self.default_width = child.default_width if hasattr(child, 'default_width') else self.default_width
		self.default_height = child.default_height if hasattr(child, 'default_height') else self.default_height
		self.setStyleSheet("background-color: white;")
		self._child = child
		self.setCentralWidget(child)
		toolbar = QtWidgets.QToolBar('Test')
		toolbar.setStyleSheet("spacing:0px; padding: 0px; background-color: #DCDCDC;")
		toolbar.setMovable(False)
		toolbar.setIconSize(QtCore.QSize(14, 14))
		toolbar.addWidget(QtWidgets.QLabel(title))
		toolbar.addWidget(HSpacer())
		toolbar.addAction(
			IconAction(self, 'SP_TitleBarNormalButton', self.onMaximize)
		)
		toolbar.addAction(
			IconAction(self, 'SP_TitleBarCloseButton', self.onClose)
		)
		self.addToolBar(toolbar)
		self._onMaximize = lambda: None
		self._onClose = lambda: None

	def onClose(self):
		self._onClose()

	def onMaximize(self):
		self._onMaximize()

	def sizeHint(self):
		return QtCore.QSize(self.default_width, self.default_height)

	def wheelEvent(self, evt):
		# Pass scroll to parent
		evt.ignore() 