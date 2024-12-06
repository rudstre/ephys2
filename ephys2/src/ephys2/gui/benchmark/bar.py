'''
Widget for rendering bar graphs
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
from matplotlib.figure import Figure
from typing import List, Optional
import matplotlib.pyplot as plt
import seaborn as sns

from ephys2.gui.utils import *

class BarGraphWidget(MatplotlibWidget):

	def __init__(self, *args, x: List[str]=[], y: List[float]=[], title: Optional[str]=None, **kwargs):
		self._x = x
		self._y = y
		self._title = title
		super().__init__(*args, fig=self._makeFigure(), **kwargs)

	def setData(self, x: Optional[List[str]]=None, y: Optional[List[float]]=None, title: Optional[str]=None):
		if x != None: self._x = x
		if y != None: self._y = y
		if title != None: self._title = title
		self.setFigure(self._makeFigure())

	def _makeFigure(self) -> Figure:
		fig, ax = plt.subplots()
		sns.barplot(x=self._x, y=self._y, ax=ax)
		if self._title != None:
			ax.set_title(self._title)
		return fig
