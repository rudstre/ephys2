#!/bin/bash
set -e

# If on macOS, add CMake to PATH
if [[ "$(uname)" == "Darwin" ]]; then
    export PATH="/Applications/CMake.app/Contents/bin:$PATH"
fi

# Add alias for ephys2gui
alias ephys2gui='python -m ephys2.gui'

# Add alias for ephys2run
alias ephys2run='python -m ephys2.run'
