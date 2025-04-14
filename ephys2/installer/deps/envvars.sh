#!/bin/bash

# Determine OS and set variables
OS_TYPE=$(uname)
ARCH_TYPE=$(uname -m)  # Get the machine hardware name
if [[ "$OS_TYPE" == "Darwin" ]]; then
    MACOS=true
    SHELL_NAME="zsh"
    RC_FILEPATH="$HOME/.zshrc"
    LOCAL_DIR="$HOME/usr/opt/local"
    CONDA_DOWNLOAD_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-$(uname -m).sh"
    CMAKE_DOWNLOAD_URL="https://github.com/Kitware/CMake/releases/download/v3.27.4/cmake-3.27.4-macos-universal.tar.gz"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    MACOS=false
    SHELL_NAME="bash"
    RC_FILEPATH="$HOME/.bashrc"
    LOCAL_DIR="/usr/local"
    CONDA_DOWNLOAD_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    CMAKE_DOWNLOAD_URL=""  # Not used on Linux
else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

PREFIX="$HOME/tmp_ephys2"
CONDA_INSTALL_SCRIPT_PATH="$PREFIX/conda_install_script.sh"
PYTHON_VERSION="3.9.7"
CMAKE_SOURCE_PATH="$PREFIX/cmake_source"
MPI_DOWNLOAD_URL="https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.1.tar.gz"
HDF_DOWNLOAD_URL="https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.14/hdf5-1.14.3/src/hdf5-1.14.3.tar.gz"
CONDA_INSTALL_DIR="$HOME/miniforge3"  # Default conda install directory
CONDA_PATH_OLD="$HOME/anaconda3"

# Export variables
export MACOS
export ARCH_TYPE
export SHELL_NAME
export LOCAL_DIR
export CONDA_DOWNLOAD_URL
export CMAKE_DOWNLOAD_URL
export PREFIX
export CONDA_INSTALL_SCRIPT_PATH
export PYTHON_VERSION
export CMAKE_SOURCE_PATH
export MPI_DOWNLOAD_URL
export HDF_DOWNLOAD_URL
export CONDA_INSTALL_DIR
export CONDA_PATH_OLD
export RC_FILEPATH

# Ensure the user owns the LOCAL_DIR
sudo mkdir -p "$LOCAL_DIR"
sudo chown -R "$USER" "$LOCAL_DIR"
sudo chmod -R 755 "$LOCAL_DIR"
