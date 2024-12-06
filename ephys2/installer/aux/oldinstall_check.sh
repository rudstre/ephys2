#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define Log File
LOG_FILE="${SCRIPT_DIR}/install_uninstall.log"

# Function to print informational messages
echo_info() {
    echo -e "\e[32m[INFO]\e[0m $1"
    echo "[INFO] $(date): $1" >> "$LOG_FILE"
}

# Function to print warning messages
echo_warning() {
    echo -e "\e[33m[WARNING]\e[0m $1"
    echo "[WARNING] $(date): $1" >> "$LOG_FILE"
}

# Function to print error messages
echo_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
    echo "[ERROR] $(date): $1" >> "$LOG_FILE"
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

# Function to remove lines containing a specific pattern from RC file
remove_from_rc() {
    local pattern="$1"
    # Use grep -v to exclude lines matching the pattern
    grep -v "$pattern" "$RC_FILEPATH" > "${RC_FILEPATH}.tmp" && mv "${RC_FILEPATH}.tmp" "$RC_FILEPATH"
}

# Function to check if OpenMPI is installed
check_openmpi() {
    # Define potential installation prefixes
    OPENMPI_PREFIXES=("/usr/local" "/opt" "$PREFIX" "$HOME/local")
    
    # Function to find OpenMPI installation directory
    find_openmpi_installation() {
        local name="openmpi"
        for prefix in "${OPENMPI_PREFIXES[@]}"; do
            if [ -d "$prefix/$name" ]; then
                echo "$prefix/$name"
                return 0
            fi
            if [ -f "$prefix/bin/mpicc" ] || [ -f "$prefix/bin/mpirun" ]; then
                echo "$prefix"
                return 0
            fi
        done
        return 1
    }
    
    openmpi_install_dir=$(find_openmpi_installation)
    
    if [ -n "$openmpi_install_dir" ]; then
        echo_warning "Detected existing OpenMPI installation at $openmpi_install_dir."
        echo_warning "It's recommended to run the uninstaller before proceeding with a new installation."
        read -rp "Do you want to run the uninstaller now? [y/N]: " run_uninstaller_openmpi
    
        if [[ "$run_uninstaller_openmpi" =~ ^[Yy]$ ]]; then
            "$SCRIPT_DIR/uninstall.sh"
            echo_info "OpenMPI uninstallation completed. Proceeding with new installation."
        else
            echo_error "Please run the uninstaller manually before proceeding."
            exit 1
        fi
    fi
}

# Function to check if HDF5 is installed
check_hdf5() {
    # Define potential installation prefixes
    HDF5_PREFIXES=("/usr/local" "/opt" "$PREFIX" "$HOME/local")
    
    # Function to find HDF5 installation directory
    find_hdf5_installation() {
        local name="hdf5"
        for prefix in "${HDF5_PREFIXES[@]}"; do
            if [ -d "$prefix/$name" ]; then
                echo "$prefix/$name"
                return 0
            fi
            if [ -f "$prefix/bin/h5cc" ] || [ -f "$prefix/bin/h5dump" ]; then
                echo "$prefix"
                return 0
            fi
        done
        return 1
    }
    
    hdf5_install_dir=$(find_hdf5_installation)
    
    if [ -n "$hdf5_install_dir" ]; then
        echo_warning "Detected existing HDF5 installation at $hdf5_install_dir."
        echo_warning "It's recommended to run the uninstaller before proceeding with a new installation."
        read -rp "Do you want to run the uninstaller now? [y/N]: " run_uninstaller_hdf5
    
        if [[ "$run_uninstaller_hdf5" =~ ^[Yy]$ ]]; then
            "$SCRIPT_DIR/uninstall.sh"
            echo_info "HDF5 uninstallation completed. Proceeding with new installation."
        else
            echo_error "Please run the uninstaller manually before proceeding."
            exit 1
        fi
    fi
}

# -------------- Pre-installation Checks --------------

# 1. Check if PREFIX directory exists
if [ -d "$PREFIX" ]; then
    echo_warning "Detected existing PREFIX directory at $PREFIX."
    echo_warning "It's recommended to run the uninstaller before proceeding with a new installation."
    read -rp "Do you want to run the uninstaller now? [y/N]: " run_uninstaller

    if [[ "$run_uninstaller" =~ ^[Yy]$ ]]; then
        "$SCRIPT_DIR/uninstall.sh"
        echo_info "Uninstallation completed. Proceeding with new installation."
    else
        echo_error "Please run the uninstaller manually before proceeding."
        exit 1
    fi
fi

# 2. Check for Conda environment 'ephys2'
if [ -d "$CONDA_PATH" ]; then
    source "$CONDA_PATH/bin/activate" || true
    if conda info --envs | grep -q "$CONDA_ENV_NAME"; then
        echo_warning "Detected existing Conda environment '$CONDA_ENV_NAME'."
        echo_warning "It's recommended to run the uninstaller before proceeding with a new installation."
        read -rp "Do you want to run the uninstaller now? [y/N]: " run_uninstaller_conda_env

        if [[ "$run_uninstaller_conda_env" =~ ^[Yy]$ ]]; then
            "$SCRIPT_DIR/uninstall.sh"
            echo_info "Conda environment uninstallation completed. Proceeding with new installation."
        else
            echo_error "Please run the uninstaller manually before proceeding."
            exit 1
        fi
    fi
fi

# 3. Check for entire Conda installation
if [ -d "$CONDA_PATH" ]; then
    echo_warning "Detected existing Conda installation at $CONDA_PATH."
    echo_warning "It's recommended to run the uninstaller before proceeding with a new installation."
    read -rp "Do you want to run the uninstaller now? [y/N]: " run_uninstaller_conda_install

    if [[ "$run_uninstaller_conda_install" =~ ^[Yy]$ ]]; then
        "$SCRIPT_DIR/uninstall.sh"
        echo_info "Conda installation uninstallation completed. Proceeding with new installation."
    else
        echo_error "Please run the uninstaller manually before proceeding."
        exit 1
    fi
fi

# 6. Check for OpenMPI installation
check_openmpi

# 7. Check for HDF5 installation
check_hdf5

# -------------- Proceed with Installation --------------

echo_info "No remnants of previous installation detected. Proceeding with installation."