'''
Multi-curve widget
'''
from typing import Optional
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt

class MultiCurvePlotter:

  def __init__(self, plot, max_curves: int, *plot_args, **plot_kwargs):
    self.plot = plot
    self.curves = np.array([
      pg.PlotCurveItem(*plot_args, **plot_kwargs) for _ in range(max_curves)
    ], dtype=object)
    for curve in self.curves:
      self.plot.addItem(curve)

  def setData(self, x: Optional[npt.NDArray]=None, y: Optional[npt.NDArray]=None, pen=None):
    if x is None or y is None:
      for curve in self.curves:
        curve.setData()
    else:
      assert x.ndim == 1
      assert x.size == y.shape[1]
      assert y.ndim == 2, 'y should be 2-dimensional'
      N = min(y.shape[0], self.curves.size)
      for i in range(N):
        if not pen is None:
          if type(pen) is np.ndarray:
            self.curves[i].setData(x, y[i], pen=pen[i])
          else:
            self.curves[i].setData(x, y[i], pen=pen)
        else:
          self.curves[i].setData(x, y[i])
      for i in range(N, self.curves.size):
        self.curves[i].setData() # Hide the remaining curves

  def forEach(self, func):
    for curve in self.curves:
      func(curve)