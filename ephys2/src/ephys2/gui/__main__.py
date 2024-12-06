'''
Ephys2 GUI entry point
'''
import argparse

# Get arguments and set settings
from ephys2.lib.settings import global_settings
global_settings.mpi_enabled = False

parser = argparse.ArgumentParser(description='Ephys2 GUI command-line interface')
parser.add_argument('-p', '--profile', help='Profile the GUI operation', action='store_true', default=False)
parser.add_argument('-d', '--debug', help='Run the GUI with debug checks', action='store_true', default=False)
args = parser.parse_args()

if args.profile:
	print('Running with profiling enabled.')
	global_settings.gui_profiling_on = True

if args.debug:
	print('Running with debug checks enabled.')
	global_settings.debug_on = True

# Run GUI
from .run import run_gui
run_gui()
