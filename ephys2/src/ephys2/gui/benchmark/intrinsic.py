'''
Viewer for intrinsic benchmarks
'''

from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QShortcut
from qtpy.QtGui import QKeySequence
import pyqtgraph as pg
from typing import List
import matplotlib.pyplot as plt
import seaborn as sns

from ephys2.gui.utils import *
from ephys2.pipeline.benchmark.intrinsic import *

from .stats import *
from .bar import *
from .intrinsic_store import *

class IntrinsicBenchmarkWidget(VScrollArea):
	
	def __init__(self, benchmarks: List[IntrinsicBenchmark], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.store = IntrinsicBenchmarkStore(benchmarks)

		# Plot styling
		sns.set_theme(
			style='whitegrid',
			palette='pastel',
			font_scale=0.4
		)

		# UI Elements
		self._chgroupSelector = pg.ComboBox()
		self._chgroupSelector.addItems([str(i) for i in self.store['chgroups']])
		self._addRow([H3Label(f'Dataset: <b>{self.store["dataset"]}</b>')])
		self._addRow([H3Label(f'Pipelines: <b>{self.store["methods"]}</b>')])
		self._addRow([H3Label('Channel group:'), self._chgroupSelector])

		# Overall metrics
		self._addRow([H3Label('Overall metrics:')])
		self._pr = SummaryStatsWidget(title='Stability')
		self._nu = SummaryStatsWidget(title='# Units')
		self._addRow([self._pr, self._nu], scrollable=True)

		# Per-unit metrics
		self._pum_layouts = dict()
		for method in self.store['methods']:
			self._addRow([H3Label(f'Per-unit metrics for pipeline: <b>{method}</b>')])
			self._pum_layouts[method] = self._addRow([], scrollable=True)

		# Listeners
		self.store.subscribe('current_chgroup', lambda: self._chgroupSelector.setValue(str(self.store['current_chgroup'])))
		self.store.subscribe('benchmarks', lambda: self._redrawBenchmarks())
		self._chgroupSelector.currentIndexChanged.connect(lambda _: self.store.dispatch(GUIAction(tag='set_chgroup', payload=int(self._chgroupSelector.currentText()))))
		self.uShortcut = QShortcut(QKeySequence('Up'), self)
		self.uShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='up', payload=None)))
		self.dShortcut = QShortcut(QKeySequence('Down'), self)
		self.dShortcut.activated.connect(lambda: self.store.dispatch(GUIAction(tag='down', payload=None)))

		self._redrawBenchmarks()

	def _addRow(self, widgets: List[QtWidgets.QWidget], scrollable: bool=False) -> QtWidgets.QHBoxLayout:
		if scrollable:
			widget = HScrollArea()
			for w in widgets:
				widget._layout.addWidget(w)
			self._layout.addWidget(widget)
			return widget._layout
		else:
			widget = QtWidgets.QFrame()
			layout = HLayout()
			for w in widgets:
				layout.addWidget(w)
			widget.setLayout(layout)
			self._layout.addWidget(widget)
			return layout

	def _redrawBenchmarks(self):
		assert len(self.store['methods']) == len(self.store['benchmarks'])
		methods, benchmarks = self.store['methods'], self.store['benchmarks']
		self._pr.setData(
			x=methods,
			y=[bm.presence_ratio_statistics for bm in benchmarks]
		)
		self._nu.setData(
			x=methods,
			y=[bm.n_units_statistics for bm in benchmarks]
		)
		for method, bm in zip(methods, benchmarks):
			clear_layout(self._pum_layouts[method])
			units = sorted(list(bm.units.keys()))
			self._pum_layouts[method].addWidget(
				BarGraphWidget(x=units, y=[bm.units[u].presence_ratio for u in units], title='Stability')
			)
			self._pum_layouts[method].addWidget(
				BarGraphWidget(x=units, y=[bm.units[u].isi_violation for u in units], title='ISI violation')
			)
			self._pum_layouts[method].addWidget(
				BarGraphWidget(x=units, y=[bm.units[u].amp_violation for u in units], title='Amplitude violation')
			)
			self._pum_layouts[method].addWidget(
				SummaryStatsWidget(x=units, y=[bm.units[u].firing_rate_statistics for u in units], title='Firing rate')
			)
			self._pum_layouts[method].addWidget(
				SummaryStatsWidget(x=units, y=[bm.units[u].peak_statistics for u in units], title='Peak amplitude')
			)
			self._pum_layouts[method].addWidget(
				SummaryStatsWidget(x=units, y=[bm.units[u].snr_statistics for u in units], title='SNR')
			)
			# self._pum_layouts[method].addWidget(
			# 	SummaryStatsWidget(x=units, y=[bm.units[u].nn_isolation_statistics for u in units], title='Isolation (NN)')
			# )

