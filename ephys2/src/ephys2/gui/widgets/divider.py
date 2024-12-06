'''
Positionable data divider.
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import QPointF, Qt, Signal, QObject
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt

from ephys2.gui.utils import *

class SelectionDivider(QObject):
    complete = Signal()

    def __init__(self, plot: pg.PlotItem):
        self._plot = plot
        self._vline = pg.InfiniteLine(angle=90, movable=False, pen='black')
        self._completed = False
        super().__init__()

    def setEnabled(self, enabled: bool):
        self._completed = False
        remove_item_if_exists(self._plot, self._vline)
        if enabled:
            self._plot.addItem(self._vline)
            self._plot.scene().sigMouseMoved.connect(self.mouseMoved)
            self._plot.scene().sigMouseClicked.connect(self.mouseClicked)
        else:
            disconnect_if_connected(self._plot.scene().sigMouseMoved, self.mouseMoved)
            disconnect_if_connected(self._plot.scene().sigMouseClicked, self.mouseClicked)
        
    def mouseMoved(self, pos: QPointF):
        x = self._plot.vb.mapSceneToView(pos).x()
        self._vline.setPos(x)

    def mouseClicked(self, evt: QtGui.QMouseEvent):
        self._completed = True
        self._plot.scene().sigMouseMoved.disconnect(self.mouseMoved)
        self._plot.scene().sigMouseClicked.disconnect(self.mouseClicked)
        self.complete.emit()

    def getStartIndex(self, xs: npt.NDArray[float]) -> int:
        assert self._completed
        return np.searchsorted(xs, self._vline.value(), side='right')