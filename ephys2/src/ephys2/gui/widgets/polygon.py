'''
Drawable polygon widget.
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import QPointF, Qt, Signal, QObject
from qtpy.QtWidgets import QApplication, QGraphicsPathItem
import pyqtgraph as pg
from shapely.geometry import Point as SPoint
from shapely.geometry.polygon import Polygon as SPolygon
import numpy as np
import numpy.typing as npt

import ephys2.gui.colors as gc
from ephys2.gui.utils import *

class SelectionPolygon(QObject):
    complete = Signal()
    vertex_size = 10
    snap_distance = 15

    def __init__(self, plot: pg.PlotItem):
        self._plot = plot
        self._polygon = pg.PlotDataItem(symbol='o', symbolSize=self.vertex_size)
        self._fill_in = None
        self.setEnabled(False)
        self.setColorIndex()
        super().__init__()

    def setColorIndex(self, color_index: int=0):
        self._color_index = color_index
        i = color_index % gc.n_colors
        pp = gc.primary_pens[i]
        pb = gc.primary_brushes[i]
        sb = gc.secondary_brushes[i]
        self._polygon.setPen('black')
        self._polygon.setBrush('black')
        self._polygon.setSymbolBrush(pg.mkBrush(None))
        self._polygon.setSymbolPen('black')
        if not (self._fill_in is None):
            self._fill_in.setBrush(sb)

    def setEnabled(self, enabled: bool):
        self._points_x = []
        self._origin_x = None
        self._points_y = []
        self._origin_y = None
        self._completed = False
        self._polygon.setData(x=[], y=[])
        remove_item_if_exists(self._plot, self._polygon)
        if not (self._fill_in is None):
            remove_item_if_exists(self._plot, self._fill_in)
        
        if enabled:
            self._plot.addItem(self._polygon)
            self._plot.scene().sigMouseMoved.connect(self.mouseMoved)
            self._plot.scene().sigMouseClicked.connect(self.mouseClicked)
        else:
            disconnect_if_connected(self._plot.scene().sigMouseMoved, self.mouseMoved)
            disconnect_if_connected(self._plot.scene().sigMouseClicked, self.mouseClicked)

    def mouseMoved(self, pos: QPointF):
        sx, sy = pos.x(), pos.y()
        pos = self._plot.vb.mapSceneToView(pos)
        px, py = pos.x(), pos.y()
        Np = len(self._points_x)
        if Np == 0:
            self._origin_x = sx
            self._origin_y = sy
        elif Np > 1 and abs(sx - self._origin_x) < self.snap_distance and abs(sy - self._origin_y) < self.snap_distance:
            px = self._points_x[0]
            py = self._points_y[0]
        self._polygon.setData(
            x=self._points_x + [px], 
            y=self._points_y + [py]
        )
    
    def mouseClicked(self, evt: QtGui.QMouseEvent):
        spos = evt.scenePos()
        pos = evt.pos()
        sx, sy = spos.x(), spos.y()
        px, py = pos.x(), pos.y()
        Np = len(self._points_x)
        if Np > 1 and abs(sx - self._origin_x) < self.snap_distance and abs(sy - self._origin_y) < self.snap_distance:
            # Finish polygon and fill
            px = self._points_x[0]
            py = self._points_y[0]
            self._points_x.append(px)
            self._points_y.append(py)
            self._plot.scene().sigMouseMoved.disconnect(self.mouseMoved)
            self._plot.scene().sigMouseClicked.disconnect(self.mouseClicked)
            self._completed = True
            self._fill_in = FilledPolygon(np.array(self._points_x), np.array(self._points_y))
            self.setColorIndex(self._color_index)
            self._plot.addItem(self._fill_in)
            self.complete.emit()
        else:
            self._points_x.append(px)
            self._points_y.append(py)
        self._polygon.setData(x=self._points_x, y=self._points_y)

    def getContainedIndices(self, xs: npt.NDArray[float], ys: npt.NDArray[float]) -> npt.NDArray[int]:
        '''
        Filter data using the polygon, returning indices.
        '''
        if self._completed:
            spoly = SPolygon(zip(self._points_x, self._points_y))
            return np.array([i for i, (x, y) in enumerate(zip(xs, ys)) if (spoly.contains(SPoint(x, y)))], dtype=np.int64)
        else:
            return np.arange(xs.shape[0], dtype=np.int64)

class FilledPolygon(QGraphicsPathItem):

    def __init__(self, x: npt.NDArray, y: npt.NDArray):
        path = pg.arrayToQPath(x, y, connect='all')
        super().__init__(path)
        self.setPen(pg.mkPen(None))