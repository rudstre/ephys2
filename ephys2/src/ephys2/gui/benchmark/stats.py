'''
Widget for rendering summary statistics
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
from matplotlib.figure import Figure
from typing import List, Optional
import matplotlib.pyplot as plt
import seaborn as sns

from ephys2.lib.metrics import *
from ephys2.gui.utils import *

class SummaryStatsWidget(MatplotlibWidget):

	def __init__(self, *args, x: List[str]=[], y: List[SummaryStats]=[], title: Optional[str]=None, **kwargs):
		self._x = x
		self._y = y
		self._title = title
		super().__init__(*args, fig=self._makeFigure(), **kwargs)

	def setData(self, x: Optional[List[str]]=None, y: Optional[List[SummaryStats]]=None, title: Optional[str]=None):
		if x != None: self._x = x
		if y != None: self._y = y
		if title != None: self._title = title
		self.setFigure(self._makeFigure())

	def _makeFigure(self) -> Figure:
		fig, ax = plt.subplots()
		assert len(self._x) == len(self._y)
		if len(self._x) > 0:
			ax.bxp(
				[
					{'med': ss.median, 'q1': ss.q1, 'q3': ss.q3, 'whislo': ss.min, 'whishi': ss.max, 'mean': ss.mean, 'label': label}
					for (label, ss) in zip(self._x, self._y)
				],
				showfliers=False,
				showmeans=True,
				meanline=True
			)
		if self._title != None:
			ax.set_title(self._title)
		return fig

