import sys
from qtpy import QtWidgets

from .home import *

def run_gui(default_directory='.'):
	app = QtWidgets.QApplication(sys.argv)
	win = HomePage(default_directory=default_directory)
	win.show()
	sys.exit(app.exec())