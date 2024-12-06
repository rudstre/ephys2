#!/bin/bash
set -e

# If on macOS, remove CMake from PATH
if [[ "$(uname)" == "Darwin" ]]; then
    # Remove /Applications/CMake.app/Contents/bin from PATH
    PATH_WITHOUT_CMAKE="${PATH//\/Applications\/CMake.app\/Contents\/bin:/}"
    PATH_WITHOUT_CMAKE="${PATH_WITHOUT_CMAKE//\/Applications\/CMake.app\/Contents\/bin/}"
    # Clean up any leading or trailing colons
    PATH_WITHOUT_CMAKE="${PATH_WITHOUT_CMAKE#:}"
    PATH_WITHOUT_CMAKE="${PATH_WITHOUT_CMAKE%:}"
    # Replace any occurrence of '::' with ':'
    PATH_WITHOUT_CMAKE="${PATH_WITHOUT_CMAKE//::/:}"
    export PATH="$PATH_WITHOUT_CMAKE"
fi

# Remove alias for ephys2gui
unalias ephys2gui 2>/dev/null

# Remove alias for ephys2run
unalias ephys2run 2>/dev/null
