#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo_info() {
    printf "\033[32m[INFO]\033[0m %s\n" "$1"
}

echo_warning() {
    printf "\033[33m[WARNING]\033[0m %s\n" "$1"
}

echo_error() {
    printf "\033[31m[ERROR]\033[0m %s\n" "$1"
}

# Source the environment variables from envvars.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_VARS_SCRIPT="${SCRIPT_DIR}/envvars.sh"

if [ -f "$ENV_VARS_SCRIPT" ]; then
    # shellcheck source=/dev/null
    source "$ENV_VARS_SCRIPT"
    echo_info "Sourced environment variables from envvars.sh"
else
    echo_error "envvars.sh not found in $SCRIPT_DIR. Exiting."
    exit 1
fi

# Backup RC file before making changes
RC_FILEPATH_BACKUP="${RC_FILEPATH}.backup_uninstall_$(date +%s)"
cp "$RC_FILEPATH" "$RC_FILEPATH_BACKUP"
echo_info "Backup of RC file created at $RC_FILEPATH_BACKUP"

# Function to remove lines containing a specific pattern from RC file
remove_from_rc() {
    local pattern="$1"
    # Use grep -v to exclude lines matching the pattern
    grep -v "$pattern" "$RC_FILEPATH" > "${RC_FILEPATH}.tmp" && mv "${RC_FILEPATH}.tmp" "$RC_FILEPATH"
}

# Conda Environment or Entire Installation Removal
echo_info "Conda Removal Options:"
echo "1. Remove only the 'ephys2' Conda environment"
echo "2. Remove the entire Conda installation"
read -rp "Please enter your choice [1 or 2]: " conda_choice

if [ "$conda_choice" == "1" ]; then
    if [ -d "$CONDA_PATH_OLD" ]; then
        source "$CONDA_PATH_OLD/bin/activate" || true
        echo_info "Removing Conda environment '$CONDA_ENV_NAME'"
        conda deactivate || true
        conda env remove -n "$CONDA_ENV_NAME" -y
    else
        echo_warning "Conda installation not found at $CONDA_PATH_OLD"
    fi

    # Remove Conda environment activation from RC file
    echo_info "Removing Conda environment activation from $RC_FILEPATH"
    remove_from_rc "conda activate $CONDA_ENV_NAME"
elif [ "$conda_choice" == "2" ]; then
    if [ -d "$CONDA_PATH_OLD" ]; then
        echo_info "Removing entire Conda installation at $CONDA_PATH_OLD"
        rm -rf "$CONDA_PATH_OLD"

        # Remove Conda initialization and related environment variables from RC file
        echo_info "Removing Conda initialization and related settings from $RC_FILEPATH"
        remove_from_rc "conda init"
        remove_from_rc "export SCRIPT_PATH="
        remove_from_rc "conda activate $CONDA_ENV_NAME"
    else
        echo_warning "Conda installation not found at $CONDA_PATH_OLD"
    fi
else
    echo_error "Invalid choice. Skipping Conda removal."
fi

# Determine the number of CPU cores
NUM_CORES=$(getconf _NPROCESSORS_ONLN)
if [ -z "$NUM_CORES" ] || [ "$NUM_CORES" -lt 1 ]; then
    NUM_CORES=1
fi
echo_info "Number of CPU cores detected: $NUM_CORES"

# Define source paths 
MPI_SOURCE_PATH="$PREFIX/mpi_source"
HDF_SOURCE_PATH="$PREFIX/hdf_source"

# 4. Uninstall MPI using make uninstall
echo_info "Uninstalling MPI using make uninstall"

# Redownload MPI source
mkdir -p "$PREFIX"
curl -L -o "$PREFIX/openmpi.tar.gz" "$MPI_DOWNLOAD_URL"
mkdir -p "$MPI_SOURCE_PATH"
tar -xvzf "$PREFIX/openmpi.tar.gz" -C "$MPI_SOURCE_PATH" --strip-components 1
cd "$MPI_SOURCE_PATH"

# Configure with the same options used during installation
./configure --prefix="$LOCAL_DIR" \
            --with-libevent=internal \
            --with-hwloc=internal \
            --with-pmix=internal \
            --with-prrte=internal \
            --disable-mpi-cxx \
            --disable-mpi1-compatibility \
            --disable-dependency-tracking \
            --silent \
            CC=gcc CXX=g++
# Run make uninstall
if sudo make -j "$NUM_CORES" uninstall; then
    echo_info "MPI uninstalled successfully"
else
    echo_warning "make uninstall failed for MPI"
fi

# 5. Uninstall HDF5 using make uninstall
echo_info "Uninstalling HDF5 using make uninstall"

# Redownload HDF5 source
curl -L -o "$PREFIX/hdf5.tar.gz" "$HDF_DOWNLOAD_URL"
mkdir -p "$HDF_SOURCE_PATH"
tar -xvzf "$PREFIX/hdf5.tar.gz" -C "$HDF_SOURCE_PATH" --strip-components 2
cd "$HDF_SOURCE_PATH"

# Configure with the same options used during installation
./configure --with-zlib="$LOCAL_DIR" --disable-fortran --prefix="$LOCAL_DIR" --silent --disable-dependency-tracking CC=gcc CXX=g++

# Run make uninstall
if sudo make -j "$NUM_CORES" uninstall; then
    echo_info "HDF5 uninstalled successfully"
else
    echo_warning "make uninstall failed for HDF5"
fi

# 6. Remove MPI Environment Variables from RC file
echo_info "Removing MPI environment variables from $RC_FILEPATH"
remove_from_rc "export PATH=\"/usr/local/bin/mpicc:\$PATH\""
remove_from_rc "export LD_LIBRARY_PATH=\"/usr/local/lib/openmpi:\$LD_LIBRARY_PATH\""
remove_from_rc "export CC=\"/usr/local/bin/mpicc\""

# 8. Remove PREFIX directory
echo_info "Removing PREFIX directory at $PREFIX"
rm -rf "$PREFIX" || echo_warning "Failed to remove PREFIX directory at $PREFIX"

# 9. Clean Up Downloaded Files and Directories within PREFIX
# (Already handled by removing PREFIX)

# 10. Finalize RC File Changes
echo_info "Reloading shell configuration"
source "$RC_FILEPATH"

echo_info "Uninstallation completed successfully."
echo_warning "Please verify that all components have been removed as expected."

rm "$RC_FILEPATH_BACKUP"
