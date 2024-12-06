'''
List widget
'''
from qtpy import QtCore, QtGui, QtWidgets 
from qtpy.QtCore import Qt
from typing import List, Any, Callable

from ephys2.gui.utils import *

class ListWidget(VLayoutWidget):
	'''
	Simple utility widget for constructing & managing widgets from a list of elements
	'''
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._items = dict()

	def setItems(self, items: List[Any], widget_creator: Callable[[Any], QtWidgets.QWidget]):
		'''
		Set the items for the list. 
		- Will be rendered in the iteration order
		- Must contain unique elements
		'''
		clear_layout(self._layout)
		self._items = dict()
		for item in items:
			assert not (item in self._items)
			widget = widget_creator(item)
			self._items[item] = widget
			self._layout.addWidget(widget)

	def hideItem(self, item: Any):
		self._items[item].hide()

	def showItem(self, item: Any):
		self._items[item].show()

	def getItemWidget(self, item: Any) -> QtWidgets.QWidget:
		return self._items[item]

	def hideAll(self):
		for widget in self._items.values():
			widget.hide()

	def showAll(self):
		for widget in self._items.values():
			widget.show()

	def getVisible(self) -> List[Any]:
		return [
			item for item, widget in self._items.items()
			if not widget.isHidden()
		]

