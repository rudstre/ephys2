#!/bin/bash
set -e

# Define colors for output
RED='\033[0;31m'
NC='\033[0m' # No Color

# If on macOS, add CMake to PATH
if [[ "$(uname)" == "Darwin" ]]; then
    export PATH="/Applications/CMake.app/Contents/bin:$PATH"
fi

# Add alias for ephys2gui
alias ephys2gui='python -m ephys2.gui'

echo -e "${RED}Warning: The parallel sorting pipeline will not work with the GUI-only installation.${NC}"
