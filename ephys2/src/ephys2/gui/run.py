import sys
from qtpy import QtWidgets

from .home import *

def run_gui():
	app = QtWidgets.QApplication(sys.argv)
	win = HomePage()
	win.show()
	sys.exit(app.exec())