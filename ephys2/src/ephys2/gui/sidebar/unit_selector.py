'''
Widget for selecting visible units
'''

from typing import Set
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import numpy.typing as npt

from ephys2.lib.settings import global_settings
import ephys2.gui.colors as gc
from ephys2.gui.utils import *
from ephys2.lib.types import *
from ephys2.gui.types import *

class UnitSelectorWidget(GUIWidget, VLayoutWidget):
	default_height: int = 350

	def __init__(self, store: GUIStore, *args, **kwargs):
		GUIWidget.__init__(self, store)
		VLayoutWidget.__init__(self, *args, **kwargs)

		# Header 
		headerWidget = HLayoutWidget()
		headerWidget._layout.addWidget(QtWidgets.QLabel('Showing:'))
		headerWidget._layout.addStretch()
		self._filtersWidget = HLayoutWidget()
		self._workspaceChk = QtWidgets.QCheckBox('workspace')
		self._workspaceChk.setChecked(self.store['showing_workspace'])
		self._excludedChk = QtWidgets.QCheckBox('excluded')
		self._excludedChk.setChecked(self.store['showing_excluded'])
		self._exportedChk = QtWidgets.QCheckBox('exported')
		self._exportedChk.setChecked(self.store['showing_exported'])
		self._visibleChk = QtWidgets.QCheckBox('visible')
		self._visibleChk.setChecked(self.store['showing_visible'])
		self._hiddenChk = QtWidgets.QCheckBox('hidden')
		self._hiddenChk.setChecked(self.store['showing_hidden'])
		self._filtersWidget._layout.addWidget(self._workspaceChk)
		self._filtersWidget._layout.addWidget(self._excludedChk)
		self._filtersWidget._layout.addWidget(self._exportedChk)
		self._filtersWidget._layout.addWidget(self._visibleChk)
		self._filtersWidget._layout.addWidget(self._hiddenChk)
		headerWidget._layout.addWidget(self._filtersWidget)
		self._isolatingText = QtWidgets.QLabel('(Isolated units only - Esc to exit)')
		self._isolatingText.hide()
		headerWidget._layout.addWidget(self._isolatingText)
		self._layout.addWidget(headerWidget)

		self._layout.addWidget(QtWidgets.QLabel('Apply to selected:'))
		headerWidget2 = HLayoutWidget()
		self._workspaceBtn = QtWidgets.QPushButton('Workspace')
		self._excludeBtn = QtWidgets.QPushButton('Exclude')
		self._exportBtn = QtWidgets.QPushButton('Export') 
		headerWidget2._layout.addWidget(self._workspaceBtn)
		headerWidget2._layout.addWidget(self._excludeBtn)
		headerWidget2._layout.addWidget(self._exportBtn)
		self._layout.addWidget(headerWidget2)

		headerWidget3 = HLayoutWidget()		
		self._hideBtn =  QtWidgets.QPushButton('Hide')
		self._showBtn = QtWidgets.QPushButton('Show')
		self._isolateBtn = QtWidgets.QPushButton('Isolate')
		headerWidget3._layout.addWidget(self._hideBtn)
		headerWidget3._layout.addWidget(self._showBtn)
		headerWidget3._layout.addWidget(self._isolateBtn)
		self._layout.addWidget(headerWidget3)

		# Selected units
		self._scrollArea = VScrollArea()
		self._layout.addWidget(self._scrollArea)
		self._selectedUnitsWidget = VLayoutWidget()
		self._mergeBtn = QtWidgets.QPushButton('Merge')
		self._mergeBtn.hide()
		self._splitBtn = QtWidgets.QPushButton('Split')
		self._splitBtn.hide()
		self._selUnitsLabel = QtWidgets.QLabel('Selected units:')
		subheaderWidget1 = HLayoutWidget()
		subheaderWidget1._layout.addWidget(self._selUnitsLabel)
		subheaderWidget1._layout.addWidget(self._mergeBtn)
		subheaderWidget1._layout.addWidget(self._splitBtn)
		self._scrollArea._layout.addWidget(subheaderWidget1)
		self._scrollArea._layout.addWidget(self._selectedUnitsWidget)

		# State
		self._is_editable = global_settings.gui_tag in ['LLVMultiBatch', 'SLLVMultiBatch']

		# Callbacks
		self._workspaceChk.toggled.connect(lambda checked: self.store.dispatch(GUIAction(tag='set_showing_status', payload=('workspace', checked))))
		self._excludedChk.toggled.connect(lambda checked: self.store.dispatch(GUIAction(tag='set_showing_status', payload=('excluded', checked))))
		self._exportedChk.toggled.connect(lambda checked: self.store.dispatch(GUIAction(tag='set_showing_status', payload=('exported', checked))))
		self._visibleChk.toggled.connect(lambda checked: self.store.dispatch(GUIAction(tag='set_showing_status', payload=('visible', checked))))
		self._hiddenChk.toggled.connect(lambda checked: self.store.dispatch(GUIAction(tag='set_showing_status', payload=('hidden', checked))))
		
		self._workspaceBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='set_selected_status', payload='workspace')))
		self._excludeBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='set_selected_status', payload='excluded')))
		self._exportBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='set_selected_status', payload='exported')))

		self._hideBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='set_selected_status', payload='hidden')))
		self._showBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='set_selected_status', payload='visible')))
		self._isolateBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='set_selected_status', payload='isolated')))
		
		self._mergeBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='merge_selected')))
		self._splitBtn.clicked.connect(lambda: self.store.dispatch(GUIAction(tag='start_split')))
		
		if self._is_editable:
			self.subscribe_store('split_mode', self.on_split_mode_update)
		self.subscribe_store('selected_units', self.on_units_change)
		self.subscribe_store('excluded_units', self.on_units_change)
		self.subscribe_store('exported_units', self.on_units_change)
		self.subscribe_store('hidden_units', self.on_units_change)
		self.subscribe_store('isolated_units', self.on_isolated_units_change)

		self.subscribe_store('showing_visible', self.on_showing_status_change)
		self.subscribe_store('showing_hidden', self.on_showing_status_change)
		self.subscribe_store('showing_excluded', self.on_showing_status_change)
		self.subscribe_store('showing_workspace', self.on_showing_status_change)
		self.subscribe_store('showing_exported', self.on_showing_status_change)

	def on_toggle_label(self, label: np.int64, visible: bool):
		deselected = self.store['hidden_units']
		if visible and label in deselected:
			deselected.remove(label)
			self.store.dispatch(GUIAction(tag='set_hidden_units', payload=deselected))
		elif (not visible) and not (label in deselected):
			deselected.add(label)
			self.store.dispatch(GUIAction(tag='set_hidden_units', payload=deselected))

	def on_exclude_label(self, label: np.int64, excluded: bool):
		excluded_units = self.store['excluded_units']
		if excluded and not (label in excluded_units):
			excluded_units.add(label)
			self.on_set_excluded(excluded_units)
		elif (not excluded) and (label in excluded_units):
			excluded_units.remove(label)
			self.on_set_excluded(excluded_units)

	def on_units_change(self):
		hidden = self.store['hidden_units']
		excluded = self.store['excluded_units'] 
		exported = self.store['exported_units'] 
		selected = self.store['selected_units'] 
		nsel = len(selected)

		# Clear layout & rebuild list
		self.deselect_all()
		def create_widget(lb: int) -> QtWidgets.QWidget:
			color = gc.colorwheel_hex[lb % 256]
			widget = HLayoutWidget()
			widget.setStyleSheet(f'color: {color}')
			widget._layout.addWidget(QtWidgets.QLabel(f'Unit {lb}'))
			widget._layout.addStretch()
			visible_box = QtWidgets.QCheckBox('visible')
			visible_box.setChecked(not (lb in hidden))
			visible_box.toggled.connect(lambda checked: self.store.dispatch(GUIAction(tag='set_unit_visibility', payload=(lb, checked))))
			widget._layout.addWidget(visible_box)
			workspaceBtn = QtWidgets.QRadioButton('workspace')
			workspaceBtn.setChecked(not (lb in exported or lb in excluded))
			workspaceBtn.toggled.connect(lambda: self.set_unit_status(lb))
			excludedBtn = QtWidgets.QRadioButton('excluded')
			excludedBtn.setChecked(lb in excluded)
			excludedBtn.toggled.connect(lambda: self.set_unit_status(lb))
			exportedBtn = QtWidgets.QRadioButton('exported')
			exportedBtn.setChecked(lb in exported)
			exportedBtn.toggled.connect(lambda: self.set_unit_status(lb))
			widget._layout.addWidget(workspaceBtn)
			widget._layout.addWidget(excludedBtn)
			widget._layout.addWidget(exportedBtn)
			return widget
		for lb in selected:
			self._selectedUnitsWidget._layout.addWidget(create_widget(lb))
		self._selUnitsLabel.setText(f'Selected units ({nsel}):')
		if nsel > 0 and self._is_editable:
			if nsel > 1:
				self._mergeBtn.show()
			else:
				self._splitBtn.show()

	def on_isolated_units_change(self):
		isolated = self.store['isolated_units']
		if isolated is None:
			self._isolatingText.hide()
			self._filtersWidget.show()
		else:
			self._isolatingText.show()
			self._filtersWidget.hide()

	def deselect_all(self):
		self._selectedUnitsWidget.clearLayout()
		self._mergeBtn.hide()
		self._splitBtn.hide()

	def on_split_mode_update(self):
		on = self.store['split_mode']
		if on:
			self.setEnabled(False)
			self.setStyleSheet("background-color: #f0f0f0")
		else:
			self.setEnabled(True)
			self.setStyleSheet('')

	def set_unit_status(self, unit: int):
		rbtn = self.sender()
		if rbtn.isChecked():
			status = rbtn.text().lower()
			self.store.dispatch(GUIAction(tag='set_unit_status', payload=(unit, status)))

	def on_showing_status_change(self):
		self._workspaceChk.blockSignals(True)
		self._excludedChk.blockSignals(True)
		self._exportedChk.blockSignals(True)
		self._visibleChk.blockSignals(True)
		self._hiddenChk.blockSignals(True)
		self._workspaceChk.setChecked(self.store['showing_workspace'])
		self._excludedChk.setChecked(self.store['showing_excluded'])
		self._exportedChk.setChecked(self.store['showing_exported'])
		self._visibleChk.setChecked(self.store['showing_visible'])
		self._hiddenChk.setChecked(self.store['showing_hidden'])
		self._workspaceChk.blockSignals(False)
		self._excludedChk.blockSignals(False)
		self._exportedChk.blockSignals(False)
		self._visibleChk.blockSignals(False)
		self._hiddenChk.blockSignals(False)
