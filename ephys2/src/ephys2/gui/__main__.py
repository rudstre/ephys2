'''
Ephys2 GUI entry point
'''
import argparse
from .run import run_gui
from ephys2.lib.settings import global_settings

def main():
    # Initialize settings
    global_settings.mpi_enabled = False

    # Parse arguments
    parser = argparse.ArgumentParser(description='Ephys2 GUI command-line interface')
    parser.add_argument('-p', '--profile', help='Profile the GUI operation', action='store_true', default=False)
    parser.add_argument('-d', '--debug', help='Run the GUI with debug checks', action='store_true', default=False)
    parser.add_argument('--default-directory', default='.', help='Default directory for file dialog')
    args = parser.parse_args()

    # Apply settings
    if args.profile:
        print('Running with profiling enabled.')
        global_settings.gui_profiling_on = True

    if args.debug:
        print('Running with debug checks enabled.')
        global_settings.debug_on = True

    # Run GUI
    run_gui(default_directory=args.default_directory)

if __name__ == '__main__':
    main()
