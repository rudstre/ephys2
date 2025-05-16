#!/bin/bash

# Determine OS and set variables
OS_TYPE=$(uname)
ARCH_TYPE=$(uname -m)  # Get the machine hardware name

# Determine current shell
CURRENT_SHELL_PATH="${SHELL:-/bin/sh}" # Default to /bin/sh if SHELL is not set
SHELL_BASENAME=$(basename "$CURRENT_SHELL_PATH")

if [[ "$OS_TYPE" == "Darwin" ]]; then
    MACOS=true
    # Default to zsh on modern macOS, but allow for bash
    if [[ "$SHELL_BASENAME" == "bash" ]]; then
        SHELL_NAME="bash"
    else
        SHELL_NAME="zsh"
    fi
    CONDA_DOWNLOAD_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-$(uname -m).sh"
    CMAKE_DOWNLOAD_URL="https://github.com/Kitware/CMake/releases/download/v3.27.4/cmake-3.27.4-macos-universal.tar.gz"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    MACOS=false
    # Default to bash on Linux, allow for zsh
    if [[ "$SHELL_BASENAME" == "zsh" ]]; then
        SHELL_NAME="zsh"
    else
        SHELL_NAME="bash"
    fi
    CONDA_DOWNLOAD_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    CMAKE_DOWNLOAD_URL=""  # Not used on Linux
else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

PREFIX="$HOME/tmp_ephys2"
CONDA_INSTALL_SCRIPT_PATH="$PREFIX/conda_install_script.sh"
PYTHON_VERSION="3.12.0"
CMAKE_SOURCE_PATH="$PREFIX/cmake_source"
MPI_DOWNLOAD_URL="https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.2.tar.gz"
HDF_DOWNLOAD_URL="https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.14/hdf5-1.14.3/src/hdf5-1.14.3.tar.gz"
H5PY_SOURCE_PATH="$PREFIX/h5py_source"
CONDA_INSTALL_DIR="$HOME/miniforge3"  # Default conda install directory

# Export variables
export MACOS
export ARCH_TYPE
export SHELL_NAME
export CONDA_DOWNLOAD_URL
export CMAKE_DOWNLOAD_URL
export PREFIX
export CONDA_INSTALL_SCRIPT_PATH
export PYTHON_VERSION
export CMAKE_SOURCE_PATH
export MPI_DOWNLOAD_URL
export HDF_DOWNLOAD_URL
export H5PY_SOURCE_PATH
export CONDA_INSTALL_DIR