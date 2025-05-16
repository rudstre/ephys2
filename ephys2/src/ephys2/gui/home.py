'''
Home screen for ephys2 GUI
'''

from ctypes import resize
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Qt
import os
import traceback

from ephys2.lib.types import *
from ephys2.lib.h5.utils import *
from ephys2.lib.settings import global_settings

from .types import *
from .utils import *
from .sbatch.widget import *
from .vbatch.widget import *
from .lvbatch.widget import *
from .llvbatch.widget import *
from .ltbatch.widget import *
from .tbatch.widget import *
from .sllvbatch.widget import *
from .rhd.widget import *
from .ofps.widget import *
from .benchmark.widget import *

class HomeWidget(QtWidgets.QLabel):
	def __init__(self):
		super().__init__('To get started, select File... Open or press Ctrl+O.')
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class HomePage(QtWidgets.QMainWindow):

	def __init__(self, default_directory='.', *args, **kwargs):
		super().__init__(*args, **kwargs)
		pg.setConfigOptions(antialias=True, useOpenGL=False) # Antialiasing for prettier plots
		self.setWindowTitle('ephys2')
		# Validate and set default directory
		self.default_directory = os.path.abspath(default_directory) if os.path.exists(default_directory) else os.path.abspath('.')
		resize_to_active_screen(self)
		self.setStyleSheet("background-color: white;")
		self.create_menu_bar()

		self.current_widget = None
		self.set_current_widget('Home')
		self.setCentralWidget(self.current_widget)

	def create_menu_bar(self):
		menuBar = self.menuBar()
		menuBar.setNativeMenuBar(False) # Forces menu within the window
		fileMenu = menuBar.addMenu('&File')

		openAction = fileMenu.addAction('&Open Ephys2 HDF5...')
		openAction.triggered.connect(self.open_file)
		openAction.setShortcut('Ctrl+O')

		openRhdAction = fileMenu.addAction('&Open Intan RHD...')
		openRhdAction.triggered.connect(self.open_rhd_file)

		openOfpsAction = fileMenu.addAction('&Open Intan one-file per signal type...')
		openOfpsAction.triggered.connect(self.open_ofps)

		openBenchmarkAction = fileMenu.addAction('&Open Ephys2 benchmark JSON...')
		openBenchmarkAction.triggered.connect(self.open_benchmark)

		exitAction = fileMenu.addAction('&Exit')
		exitAction.triggered.connect(self.close)
		exitAction.setShortcut('Ctrl+Q')

	def open_file(self):
		'''
		Open a file and determine which viewer to show based on the file type.
		'''
		if self.warned_about_unsaved_changes():
			filepaths = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open files', self.default_directory, 'Ephys2 HDF5 files (*.h5)', options=QtWidgets.QFileDialog.DontUseNativeDialog)[0]
			if all(os.path.exists(f) for f in filepaths) and len(filepaths) > 0:
				try:
					print(f'Opening files: {filepaths}')
					with open_h5s(filepaths, 'r') as files:
						tags = [f.attrs['tag'] for f in files]
						assert all(t == tags[0] for t in tags), f'Received files of different types: {tags}'
						tag = tags[0]
						print(f'Showing viewer for file type {tag}')
						global_settings.gui_tag = tag
						self.set_current_widget(tag)
						self.current_widget.set_files(filepaths)
				except:
					traceback.print_exc()
					self.show_load_error('Ephys2 HDF5 file')

	def open_rhd_file(self):
		if self.warned_about_unsaved_changes():
			filepath = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory, 'RHD2000 files (*.rhd)', options=QtWidgets.QFileDialog.DontUseNativeDialog)[0]
			if os.path.exists(filepath):
				try:
					print('Opening RHD file')
					self.set_current_widget('RHD')
					self.current_widget.set_file(filepath)
				except:
					traceback.print_exc()
					self.show_load_error('RHD file')

	def open_ofps(self):
		if self.warned_about_unsaved_changes():
			filepath = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Open directory one-file per signal type directory', self.default_directory, options=QtWidgets.QFileDialog.DontUseNativeDialog))
			if os.path.isdir(filepath):
				try:
					print('Opening OFPS directory')
					self.set_current_widget('OFPS')
					self.current_widget.set_file(filepath)
				except:
					traceback.print_exc()
					self.show_load_error('one-file per signal type directory')

	def open_benchmark(self):
		if self.warned_about_unsaved_changes():
			filepaths = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open files', self.default_directory, 'Ephys2 benchmark files (*.json)', options=QtWidgets.QFileDialog.DontUseNativeDialog)[0]
			if all(os.path.exists(f) for f in filepaths) and len(filepaths) > 0:
				try:
					print(f'Opening benchmark files: {filepaths}')
					self.set_current_widget('Benchmark')
					self.current_widget.set_files(filepaths)
				except:
					traceback.print_exc()
					self.show_load_error('Ephys2 benchmark file')

	def show_load_error(self, noun: str):
		show_error(f'There was an issue loading the {noun}. Please check the terminal logs.')

	def set_current_widget(self, tag: str):
		if not (self.current_widget is None):
			self.current_widget.deleteLater()

		Widget, Store = {
			'Home': (HomeWidget, None),
			'SBatch': (SBatchWidget, SBatchStore),
			'RHD': (RHDWidget, RHDStore),
			'OFPS': (OFPSWidget, OFPSStore),
			'VMultiBatch': (VMultiBatchWidget, VMultiBatchStore),
			'LVMultiBatch': (LVMultiBatchWidget, LVMultiBatchStore),
			'LLVMultiBatch': (LLVMultiBatchWidget, LLVMultiBatchStore),
			'LTMultiBatch': (LTMultiBatchWidget, LTMultiBatchStore),
			'TMultiBatch': (TMultiBatchWidget, TMultiBatchStore),
			'SLLVMultiBatch': (SLLVMultiBatchWidget, SLLVMultiBatchStore),
			'Benchmark': (BenchmarkWidget, None),
		}[tag]
		self.current_store = Store() if Store is not None else None
		self.current_widget = Widget() if Store is None else Widget(self.current_store)

		self.setCentralWidget(self.current_widget)

	def closeEvent(self, event):
		if self.warned_about_unsaved_changes():
			event.accept()
		else:
			event.ignore()
	
	def warned_about_unsaved_changes(self) -> bool:
		# Warn if tried to close before saving
		if (
				not (self.current_widget is None or self.current_store is None) and 
				global_settings.gui_tag in ['LLVMultiBatch', 'SLLVMultiBatch'] and
				self.current_store['edited']
			):
			if show_warning('You have unsaved changes. Are you sure you want to close?') == QtWidgets.QMessageBox.Cancel:
				return False
		return True


