#!/usr/bin/env bash
#===========================================================================
# launchGUI.sh
#
# This script checks for Conda or Micromamba, installs Micromamba if neither
# is found, ensures an 'ephys2-gui' environment exists (with xcb-util-cursor),
# activates it, and then launches the ephys2 GUI via Singularity. If no --sif
# is passed, it finds the latest ephys2-release-*.sif in RELEASE_DIR. Any
# other arguments provided to this script are forwarded directly to the GUI.
#
# Usage:
#   ./launchGUI.sh [--sif /path/to/ephys2.sif] [<gui-arg1> <gui-arg2> ...]
#
# Example:
#   ./launchGUI.sh --sif /path/to/ephys2.sif --default-directory /data/myrecording
#
#===========================================================================

set -euo pipefail

# Error trap function
error_exit() {
  local line_no=$1
  local error_code=$2
  echo "ERROR: Script failed at line $line_no with exit code $error_code"
  echo "Command that failed: ${BASH_COMMAND}"
  exit $error_code
}

# Set up error trap
trap 'error_exit ${LINENO} $?' ERR

#--------------------------
# Defaults (edit as needed)
#--------------------------
# Directory containing ephys2-release-*.sif files, if --sif is omitted
RELEASE_DIR="/n/holylabs-olveczky/Lab/singularity/releases"
# Name of the Conda/Micromamba environment
ENV_NAME="ephys2-gui"
# Required package for the GUI environment
REQUIRED_PKG="xcb-util-cursor"

#--------------------------
# Parse arguments
#--------------------------
SIF_PATH=""
# Collect any arguments that are not --sif (i.e. to pass to the GUI)
GUI_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sif)
      shift
      if [[ -z "${1:-}" ]]; then
        echo "Error: --sif requires a path argument."
        echo "Usage: $0 [--sif /path/to/ephys2.sif] [<gui-arg1> <gui-arg2> ...]"
        exit 1
      fi
      SIF_PATH="$1"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--sif /path/to/ephys2.sif] [<gui-arg1> <gui-arg2> ...]"
      exit 0
      ;;
    *)
      # Any other argument is forwarded to the GUI
      GUI_ARGS+=("$1")
      shift
      ;;
  esac
done

#--------------------------
# If no SIF_PATH provided, pick the latest ephys2-release-*.sif
#--------------------------
if [[ -z "$SIF_PATH" ]]; then
  echo "Searching for latest release in '${RELEASE_DIR}'..."
  
  if [[ ! -d "$RELEASE_DIR" ]]; then
    echo "Error: Release directory '$RELEASE_DIR' does not exist"
    exit 1
  fi
  
  latest_sif=$(ls -1 "${RELEASE_DIR}"/ephys2-release-*.sif 2>/dev/null | sort -V | tail -n1 || true)
  if [[ -z "$latest_sif" ]]; then
    echo "Error: No ephys2-release-*.sif found in '${RELEASE_DIR}'."
    ls -la "$RELEASE_DIR" || echo "Directory listing failed"
    exit 1
  fi
  SIF_PATH="$latest_sif"
  echo "Using: $SIF_PATH"
fi

#--------------------------
# Detect or install Conda/Micromamba
#--------------------------
# Source shell initialization files to ensure conda/micromamba functions are available
if [[ -f ~/.bashrc ]]; then
  source ~/.bashrc
fi
if [[ -f ~/.bash_profile ]]; then
  source ~/.bash_profile
fi

# Check for micromamba (including functions/aliases)
if command -v micromamba >/dev/null 2>&1 || type micromamba >/dev/null 2>&1; then
  PM="micromamba"
  echo "Detected Micromamba."
  # Initialize if not already done
  if ! micromamba --version >/dev/null 2>&1; then
    eval "$(micromamba shell hook -s bash)" 2>/dev/null || {
      echo "Warning: Failed to initialize micromamba"
    }
  fi
elif command -v conda >/dev/null 2>&1 || type conda >/dev/null 2>&1; then
  PM="conda"
  echo "Detected Conda."
  # Initialize if not already done
  if ! conda --version >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)" 2>/dev/null || {
      echo "Warning: Failed to initialize conda"
    }
  fi
else
  echo "Installing Micromamba..."
  
  if ! command -v curl >/dev/null 2>&1; then
    echo "Error: curl not available for downloading micromamba"
    exit 1
  fi
  
  TEMP_INSTALLER=$(mktemp)
  if ! curl -Ls https://micro.mamba.pm/install.sh -o "$TEMP_INSTALLER"; then
    echo "Error: Failed to download micromamba installer"
    rm -f "$TEMP_INSTALLER"
    exit 1
  fi
  
  # Run installer with default answers
  if ! echo -e "y\n\ny\n" | bash "$TEMP_INSTALLER"; then
    echo "Error: Micromamba installer failed"
    rm -f "$TEMP_INSTALLER"
    exit 1
  fi
  
  rm -f "$TEMP_INSTALLER"
  
  # Source the updated shell configuration
  if [[ -f ~/.bashrc ]]; then
    source ~/.bashrc
  fi
  
  PM="micromamba"
  echo "Micromamba installed successfully."
fi

# Verify package manager is working
if [[ "$PM" == "micromamba" ]]; then
  if ! micromamba --version >/dev/null 2>&1; then
    echo "Error: micromamba not working properly"
    exit 1
  fi
else
  if ! conda --version >/dev/null 2>&1; then
    echo "Error: conda not working properly"
    exit 1
  fi
fi

#--------------------------
# Ensure 'ephys2-gui' environment exists
#--------------------------
echo "Setting up environment '${ENV_NAME}'..."

# Check if environment exists (adjust awk for conda vs micromamba)
if [[ "$PM" == "micromamba" ]]; then
  env_exists=$($PM env list | awk '{print $1}' | grep -Fxq "$ENV_NAME" && echo "true" || echo "false")
else
  env_exists=$($PM env list | awk 'NF {print $1}' | grep -Fxq "$ENV_NAME" && echo "true" || echo "false")
fi

if [[ "$env_exists" == "true" ]]; then
  echo "Environment '${ENV_NAME}' already exists."
else
  echo "Creating environment with ${REQUIRED_PKG}..."
  if ! $PM create -n "$ENV_NAME" "$REQUIRED_PKG" -y; then
    echo "Error: Failed to create environment '${ENV_NAME}'"
    exit 1
  fi
fi

#--------------------------
# Activate the environment
#--------------------------
echo "Activating environment '${ENV_NAME}'..."
if ! $PM activate "$ENV_NAME"; then
  echo "Error: Failed to activate environment '${ENV_NAME}'"
  exit 1
fi

#--------------------------
# Verify SIF exists
#--------------------------
if [[ ! -f "$SIF_PATH" ]]; then
  echo "Error: Singularity image not found at '$SIF_PATH'."
  ls -la "$(dirname "$SIF_PATH")" || echo "Could not list directory"
  exit 1
fi

#--------------------------
# Verify environment is active
#--------------------------
current_env=$($PM env list | grep '*' | awk '{print $1}' || echo "")

if [[ "$current_env" != "$ENV_NAME" ]]; then
  echo "Reactivating environment..."
  $PM activate "$ENV_NAME"
fi

# Check if singularity command exists
if ! command -v singularity >/dev/null 2>&1; then
  echo "Error: singularity command not found. Please ensure Singularity is installed and in your PATH."
  exit 1
fi

#--------------------------
# Launch ephys2 GUI
#--------------------------
echo "Launching ephys2 GUI..."
if ! singularity run --bind /n "$SIF_PATH" gui "${GUI_ARGS[@]}"; then
  echo "Error: Failed to launch ephys2 GUI"
  exit 1
fi

echo "GUI session completed."
exit 0
