#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -eE -o pipefail

# --- Script Configuration and Variables ---

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Variable to hold the current step
CURRENT_STEP=""

# Paths and variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EPHYS_PATH="$(dirname "$SCRIPT_DIR")"
EPHYS_REPO="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$SCRIPT_DIR/install.log"

# Remove any existing install.log
if [ -f "$LOG_FILE" ]; then
    rm "$LOG_FILE"
fi

echo -e "${GREEN}Installation log will be saved to $LOG_FILE${NC}"

# Load environment variables (includes OS check)
source "${SCRIPT_DIR}/deps/envvars.sh"

# Number of CPU cores
NUM_CORES=$(getconf _NPROCESSORS_ONLN)
if [ -z "$NUM_CORES" ] || [ "$NUM_CORES" -lt 1 ]; then
    NUM_CORES=1
fi
echo -e "${GREEN}Number of CPU cores detected: $NUM_CORES${NC}"

# Define source paths within the Conda environment
MPI_SOURCE_PATH="$PREFIX/mpi_source"
HDF_SOURCE_PATH="$PREFIX/hdf_source"

# --- Utility Functions ---

# Function to check if the script is being sourced
is_sourced() {
    [[ "${BASH_SOURCE[0]}" != "${0}" ]]
}

# Function to handle errors
error_handler() {
    local exit_code=$?
    local line_no=$1
    local command="${BASH_COMMAND}"
    # Log the error
    echo -e "Error: Command '${command}' exited with status ${exit_code} at line ${line_no}." >> "$LOG_FILE"
    # Display the error to the user
    echo -e "${RED}Error: Command '${command}' exited with status ${exit_code} at line ${line_no}.${NC}" >&2
    echo -e "${RED}${CURRENT_STEP} (FAIL)${NC}" >&2
    echo -e "${RED}Please check the log file at '$LOG_FILE' for more details.${NC}" >&2
    if is_sourced; then
        return $exit_code
    else
        exit $exit_code
    fi
}

# Trap ERR to catch errors and call the error_handler function
trap 'error_handler ${LINENO}' ERR

# Function to print messages and set the current step
start_step() {
    CURRENT_STEP="$1"
    echo -e "${GREEN}$CURRENT_STEP${NC}"
}

# Function to print general messages
print_msg() {
    echo -e "${GREEN}$1${NC}"
}

# --- Installation Functions ---

# Function to detect existing Conda installations
detect_conda_installations() {
    conda_paths=()

    # Use 'conda info --base' if 'conda' command is available
    if command -v conda >/dev/null 2>&1; then
        conda_base=$(conda info --base)
        if [ -d "$conda_base" ]; then
            conda_paths+=("$conda_base")
        fi
    fi

    # Check common installation directories
    possible_conda_dirs=(
        "$HOME/miniforge3"
        "$HOME/miniconda3"
        "$HOME/anaconda3"
        "$HOME/miniforge"
        "$HOME/miniconda"
        "$HOME/anaconda"
    )

    for conda_dir in "${possible_conda_dirs[@]}"; do
        if [ -d "$conda_dir" ]; then
            # Check if the directory is already in conda_paths
            already_in_list=false
            for existing_dir in "${conda_paths[@]}"; do
                if [ "$existing_dir" = "$conda_dir" ]; then
                    already_in_list=true
                    break
                fi
            done

            if [ "$already_in_list" = false ]; then
                conda_paths+=("$conda_dir")
            fi
        fi
    done

    # Print each path on a new line
    for path in "${conda_paths[@]}"; do
        echo "$path"
    done
}

# Function to choose installation option
choose_install_option() {
    echo "Please choose the installation option:"
    echo "1) Install the GUI only"
    echo "2) Install the full sorting pipeline (requires building from source)"
    read -rp "Enter the number corresponding to your choice: " INSTALL_CHOICE

    if [ "$INSTALL_CHOICE" -eq 1 ]; then
        INSTALL_OPTION="GUI"
        echo "You have chosen to install the GUI only."
    elif [ "$INSTALL_CHOICE" -eq 2 ]; then
        INSTALL_OPTION="FULL"
        echo "You have chosen to install the full sorting pipeline."
    else
        echo "Invalid choice. Exiting."
        if is_sourced; then
            return 1
        else
            exit 1
        fi
    fi
}

# Function to set the Conda environment name based on installation option
set_conda_env_name() {
    if [ "$INSTALL_OPTION" = "FULL" ]; then
        CONDA_ENV_NAME="ephys2"
    elif [ "$INSTALL_OPTION" = "GUI" ]; then
        CONDA_ENV_NAME="ephys2-gui"
    fi
    echo "Conda environment name set to '$CONDA_ENV_NAME'"
}

# Function to set up temporary folder
setup_temp_folder() {
    start_step "Setting up temporary folder..."
    mkdir -p "$PREFIX" >> "$LOG_FILE" 2>&1
    # Also prepare deps folder for the patch if it doesn't exist
    mkdir -p "$SCRIPT_DIR/deps" >> "$LOG_FILE" 2>&1
}

# Function to fetch h5py patch
fetch_h5py_patch() {
    start_step "Fetching h5py patch..."
    PATCH_SOURCE_PATH="$(dirname $(dirname "$SCRIPT_DIR"))/singularity/h5py.patch"
    PATCH_DEST_PATH="$SCRIPT_DIR/deps/h5py.patch"
    if [ -f "$PATCH_SOURCE_PATH" ]; then
        cp "$PATCH_SOURCE_PATH" "$PATCH_DEST_PATH" >> "$LOG_FILE" 2>&1
        echo "h5py.patch copied to $PATCH_DEST_PATH" >> "$LOG_FILE" 2>&1
    else
        echo "Error: h5py.patch not found at $PATCH_SOURCE_PATH. This is a critical component." >> "$LOG_FILE"
        echo -e "${RED}Error: h5py.patch not found at $PATCH_SOURCE_PATH. This is a critical component. Installation cannot proceed.${NC}" >&2
        exit 1 # Exit if patch is not found
    fi
    return 0 # Indicate success
}

# Function to install build tools
install_build_tools() {
    start_step "Installing build tools..."
    if $MACOS; then
        if [ -d "/Applications/CMake.app" ]; then
            echo "CMake.app already exists in /Applications." >> "$LOG_FILE" 2>&1
            # Ensure CMake is in PATH for the current script execution
            export PATH="/Applications/CMake.app/Contents/bin:$PATH"
            echo "Ensured /Applications/CMake.app/Contents/bin is in PATH for this session." >> "$LOG_FILE" 2>&1
        else
            {
                curl -L -o "${CMAKE_SOURCE_PATH}.tar.gz" "$CMAKE_DOWNLOAD_URL"
                mkdir -p "$CMAKE_SOURCE_PATH"
                tar -xzf "${CMAKE_SOURCE_PATH}.tar.gz" -C "$CMAKE_SOURCE_PATH" --strip-components 1
                sudo mv "$CMAKE_SOURCE_PATH/CMake.app" /Applications/
                echo "CMake.app installed in /Applications."
                # Add CMake to PATH for the current script execution
                export PATH="/Applications/CMake.app/Contents/bin:$PATH"
                echo "Added /Applications/CMake.app/Contents/bin to PATH for this session."
            } >> "$LOG_FILE" 2>&1
        fi
    else
        {
            sudo apt update
            sudo apt install -y build-essential wget libxcb-cursor0
            echo "necessary libraries installed via apt."
        } >> "$LOG_FILE" 2>&1
    fi
}

# Function to install Conda
install_conda() {
    start_step "Checking for existing Conda installations..."
    # Read the output of detect_conda_installations into an array
    IFS=$'\n' read -r -d '' -a conda_paths_found < <(detect_conda_installations; printf '\0')
    num_conda_installs=${#conda_paths_found[@]}

    if [ "$num_conda_installs" -eq 0 ]; then
        echo "No existing Conda installations found."
        echo "Please choose one of the following options:"
        echo "1) Create a new Miniforge installation at the default path ($CONDA_INSTALL_DIR)"
        echo "2) Specify a different directory to install Miniforge"
        read -rp "Enter the number corresponding to your choice: " USER_CHOICE

        if [ "$USER_CHOICE" -eq 1 ]; then
            CONDA_INSTALL_PATH="$CONDA_INSTALL_DIR"
        elif [ "$USER_CHOICE" -eq 2 ]; then
            read -rp "Enter the new directory path: " CONDA_INSTALL_PATH
        else
            echo "Invalid choice. Exiting."
            if is_sourced; then
                return 1
            else
                exit 1
            fi
        fi
        install_miniforge "$CONDA_INSTALL_PATH"
    else
        echo "Found the following Conda installations:"
        for i in "${!conda_paths_found[@]}"; do
            echo "$((i+1))) ${conda_paths_found[i]}"
        done
        echo "Please choose one of the following options:"
        echo "1) Use an existing Conda installation"
        echo "2) Create a new Miniforge installation at the default path ($CONDA_INSTALL_DIR) without deleting any existing installations"
        echo "3) Delete all existing Conda installations and create a new Miniforge installation"
        read -rp "Enter the number corresponding to your choice: " USER_CHOICE

        if [ "$USER_CHOICE" -eq 1 ]; then
            echo "Select the Conda installation to use:"
            for i in "${!conda_paths_found[@]}"; do
                echo "$((i+1))) ${conda_paths_found[i]}"
            done
            read -rp "Enter the number corresponding to your choice: " INSTALL_CHOICE
            INSTALL_CHOICE=$((INSTALL_CHOICE-1))
            if [ "$INSTALL_CHOICE" -ge 0 ] && [ "$INSTALL_CHOICE" -lt "$num_conda_installs" ]; then
                CONDA_PATH="${conda_paths_found[$INSTALL_CHOICE]}"
                echo "Using Conda installation at $CONDA_PATH"
            else
                echo "Invalid choice. Exiting."
                if is_sourced; then
                    return 1
                else
                    exit 1
                fi
            fi
        elif [ "$USER_CHOICE" -eq 2 ]; then
            CONDA_INSTALL_PATH="$CONDA_INSTALL_DIR"
            install_miniforge "$CONDA_INSTALL_PATH"
        elif [ "$USER_CHOICE" -eq 3 ]; then
            echo "Deleting all existing Conda installations..."
            for conda_path in "${conda_paths_found[@]}"; do
                conda init "$SHELL_NAME" --reverse
                rm -rf "$conda_path"
                echo "Deleted $conda_path"
            done
            CONDA_INSTALL_PATH="$CONDA_INSTALL_DIR"
            install_miniforge "$CONDA_INSTALL_PATH"
        else
            echo "Invalid choice. Exiting."
            if is_sourced; then
                return 1
            else
                exit 1
            fi
        fi
    fi
}

# Function to install Miniforge at specified path
install_miniforge() {
    local install_dir="$1"
    if [ -d "$install_dir" ]; then
        echo "Conda installation directory '$install_dir' already exists."
        read -rp "Do you want to use this existing installation? (yes/no): " REPLY
        if [[ "$REPLY" =~ ^[Yy][Ee][Ss]|[Yy]$ ]]; then
            CONDA_PATH="$install_dir"
            echo "Using existing Conda installation at $CONDA_PATH"
        else
            read -rp "Enter a different directory path: " install_dir
            install_miniforge "$install_dir"
        fi
    else
        {
            curl -L -o "$CONDA_INSTALL_SCRIPT_PATH" "$CONDA_DOWNLOAD_URL"
            bash "$CONDA_INSTALL_SCRIPT_PATH" -b -p "$install_dir"
        } >> "$LOG_FILE" 2>&1
        CONDA_PATH="$install_dir"
        echo "Miniforge installed at $CONDA_PATH"
    fi
}

# Function to initialize the Conda environment
initialize_conda_environment() {
    start_step "Initializing Conda environment and installing Mamba..."

    if [ -z "$CONDA_PATH" ] || [ ! -x "$CONDA_PATH/bin/conda" ]; then
        echo -e "${RED}Error: CONDA_PATH ('$CONDA_PATH') is not set or invalid. Cannot initialize Conda environment.${NC}" >&2
        exit 1
    fi

    echo "Sourcing Conda script: $CONDA_PATH/etc/profile.d/conda.sh" >> "$LOG_FILE"
    set +e
    source "$CONDA_PATH/etc/profile.d/conda.sh"
    source_exit_code=$?
    set -e
    if [ $source_exit_code -ne 0 ]; then
        echo -e "${RED}Warning: Sourcing conda.sh returned non-zero: $source_exit_code. Proceeding cautiously.${NC}" | tee -a "$LOG_FILE"
    fi

    echo "Initializing Conda for shell $SHELL_NAME..." | tee -a "$LOG_FILE"
    if ! conda init "$SHELL_NAME" >> "$LOG_FILE" 2>&1; then
        echo -e "${RED}Warning: 'conda init $SHELL_NAME' failed. Conda might not be fully set up for future interactive sessions.${NC}" | tee -a "$LOG_FILE"
    else
        echo "Conda successfully initialized for $SHELL_NAME." | tee -a "$LOG_FILE"
    fi
    
    # Re-source the RC file to make conda activate available in the current script session if needed.
    # This is a bit dependent on how conda init behaves and if it modifies the current shell state.
    # For zsh, it typically modifies .zshrc. For bash, .bashrc.
    # We need to ensure `conda activate base` works reliably right after `conda init`.
    echo "Attempting to activate Conda base environment after conda init..." | tee -a "$LOG_FILE"
    # Try activating base. If it fails, attempt to re-source shell config and try again.
    # This complex activation logic is to make script more robust across different shell behaviors with `conda init`.
    if ! conda activate base >> "$LOG_FILE" 2>&1; then
        echo "Initial conda activate base failed. Attempting to re-source shell config..." >> "$LOG_FILE"
        RC_FILE_TO_SOURCE=""
        if [ "$SHELL_NAME" == "zsh" ]; then RC_FILE_TO_SOURCE="$HOME/.zshrc"; 
        elif [ "$SHELL_NAME" == "bash" ]; then RC_FILE_TO_SOURCE="$HOME/.bashrc"; 
        fi

        if [ -n "$RC_FILE_TO_SOURCE" ] && [ -f "$RC_FILE_TO_SOURCE" ]; then
            echo "Sourcing $RC_FILE_TO_SOURCE..." >> "$LOG_FILE"
            set +e
            source "$RC_FILE_TO_SOURCE"
            set -e
            echo "Re-sourced $RC_FILE_TO_SOURCE. Retrying conda activate base..." >> "$LOG_FILE"
            if ! conda activate base >> "$LOG_FILE" 2>&1; then
                 echo -e "${RED}Error: Failed to activate Conda base environment even after re-sourcing shell config. Check Conda installation at $CONDA_PATH.${NC}" >&2
                 exit 1
            fi
        else 
            echo -e "${RED}Error: Could not determine RC file to source, or file does not exist. Failed to activate Conda base environment.${NC}" >&2
            exit 1
        fi
    fi
    echo "Conda base environment activated." | tee -a "$LOG_FILE"

    echo "Ensuring Mamba is installed in base Conda environment..." | tee -a "$LOG_FILE"
    {
        # First ensure conda is up to date
        conda update -n base conda -y
        
        # Remove existing mamba installation if it exists
        conda remove -n base mamba -y || true
        
        # Install mamba with explicit channel priority and dependencies
        conda install -n base -c conda-forge mamba "libmamba>=0.25.0" -y
        
        # Verify mamba installation
        if ! command -v mamba >/dev/null 2>&1; then
            echo -e "${RED}Error: Mamba installation failed. Please check your Conda installation.${NC}" >&2
            exit 1
        fi
    } >> "$LOG_FILE" 2>&1 || {
        echo -e "${RED}Error: Failed to install Mamba into the base Conda environment.${NC}" >&2
        exit 1
    }
    echo "Mamba is now installed/updated in the base environment." | tee -a "$LOG_FILE"

    # With mamba installed in the active base environment and Conda initialized,
    # we will use 'conda activate' for script context switching.
  
    # Check if target environment already exists using mamba
    echo "Checking if Mamba environment '$CONDA_ENV_NAME' already exists..." | tee -a "$LOG_FILE"
    if conda env list | grep -qE "^${CONDA_ENV_NAME}(\\s|$)"; then
        # Environment exists (grep returns 0)
        echo "Mamba environment '$CONDA_ENV_NAME' already exists." | tee -a "$LOG_FILE"
        read -rp "Enter a new name for the Mamba environment, or press Enter to exit: " NEW_CONDA_ENV_NAME
        if [ -n "$NEW_CONDA_ENV_NAME" ]; then
            CONDA_ENV_NAME="$NEW_CONDA_ENV_NAME"
            echo "New environment name set to '$CONDA_ENV_NAME'." | tee -a "$LOG_FILE"
        else
            echo -e "${RED}No new environment name provided. Exiting to avoid issues with existing environment.${NC}" >&2
            exit 1 # Exit if user provides no new name for an existing env
        fi
    else
        # Environment does not exist (grep returns 1), or mamba/grep had other error
        echo "Mamba environment '$CONDA_ENV_NAME' not found. Proceeding with creation." | tee -a "$LOG_FILE"
    fi
    
    echo "Creating Mamba environment '$CONDA_ENV_NAME' with Python $PYTHON_VERSION..." | tee -a "$LOG_FILE"
    {
        conda clean --all -y
        # Create environment with conda first
        conda create -n "$CONDA_ENV_NAME" -y
        # Activate the environment
        conda activate "$CONDA_ENV_NAME"
        # Now use mamba for package management
        mamba install -n "$CONDA_ENV_NAME" -c conda-forge python="$PYTHON_VERSION" -y
    } >> "$LOG_FILE" 2>&1 || {
        echo -e "${RED}Error: Failed to create environment '$CONDA_ENV_NAME'. Check $LOG_FILE for details.${NC}" >&2
        exit 1 
    }
    echo "Environment '$CONDA_ENV_NAME' created successfully." | tee -a "$LOG_FILE"
}

# Function to install Python packages
install_python_packages() {
    start_step "Installing Python packages..."
    conda activate "$CONDA_ENV_NAME"
    if [ "$INSTALL_OPTION" = "GUI" ]; then
        {
            mamba install -c conda-forge numpy=1.26.4 scipy=1.13.1 matplotlib osqp cvxopt cython openmpi mpi4py=3.1.5 -y
        } >> "$LOG_FILE" 2>&1
        echo "Python packages installed via Conda."
    elif [ "$INSTALL_OPTION" = "FULL" ]; then
        {
            pip install --no-input numpy==1.26.4 scipy==1.13.1 matplotlib osqp cvxopt cython
        } >> "$LOG_FILE" 2>&1
        echo "Python packages installed via pip."
    fi
}

# Function to install MPI
install_mpi() {
    start_step "Downloading MPI..."
    {
        # Download OpenMPI source
        curl -L -o "${MPI_SOURCE_PATH}.tar.gz" "$MPI_DOWNLOAD_URL"
        mkdir -p "$MPI_SOURCE_PATH"
        tar -xzf "${MPI_SOURCE_PATH}.tar.gz" -C "$MPI_SOURCE_PATH" --strip-components=1
        cd "$MPI_SOURCE_PATH"
    } >> "$LOG_FILE" 2>&1
    start_step "Compiling MPI..."
    {
        # Configure and install OpenMPI
        ./configure --prefix="$CONDA_PREFIX" --with-libevent=internal --with-hwloc=internal --with-pmix=internal --with-prrte=internal
        make -j "$NUM_CORES" all
    } >> "$LOG_FILE" 2>&1
    start_step "Installing MPI..."
    {
        make -j "$NUM_CORES" install
        echo "OpenMPI installed within Conda environment at $CONDA_PREFIX"
    } >> "$LOG_FILE" 2>&1
}

# Function to install HDF5
install_hdf5() {
    start_step "Downloading HDF5..."
    {
        # Download HDF5 source
        curl -L -o "${HDF_SOURCE_PATH}.tar.gz" "$HDF_DOWNLOAD_URL"
        mkdir -p "$HDF_SOURCE_PATH"
        tar -xzf "${HDF_SOURCE_PATH}.tar.gz" -C "$HDF_SOURCE_PATH" --strip-components=2
        cd "$HDF_SOURCE_PATH"
    } >> "$LOG_FILE" 2>&1
    start_step "Compiling HDF5..."
    {
        # Configure and install HDF5
        CC=$(which mpicc) ./configure --with-zlib="$CONDA_PREFIX" --disable-fortran --prefix="$CONDA_PREFIX" --enable-shared --enable-parallel
        make -j "$NUM_CORES"
    } >> "$LOG_FILE" 2>&1
    start_step "Installing HDF5..."
    {
        make install
        echo "HDF5 installed within Conda environment at $CONDA_PREFIX"
    } >> "$LOG_FILE" 2>&1
}

# Function to install mpi4py
install_mpi4py() {
    start_step "Installing mpi4py within Conda environment..."
    {
        conda activate "$CONDA_ENV_NAME"
        pip uninstall -y mpi4py || true
        pip cache purge
        export PATH="$CONDA_PREFIX/bin:$PATH"
        MPICC=$(which mpicc) pip install --no-binary=mpi4py --no-cache-dir mpi4py==3.1.5
        echo "mpi4py installed within Conda environment."
    } >> "$LOG_FILE" 2>&1
}

# Function to install h5py
install_h5py() {
    start_step "Installing h5py with MPI support from source within Conda environment..."
    {
        conda activate "$CONDA_ENV_NAME"
        pip uninstall -y h5py || true
        pip cache purge
        
        # Clean up previous source if it exists
        if [ -d "$H5PY_SOURCE_PATH" ]; then
            rm -rf "$H5PY_SOURCE_PATH"
        fi
        mkdir -p "$H5PY_SOURCE_PATH"
        
        echo "Cloning h5py repository..." >> "$LOG_FILE"
        git clone https://github.com/h5py/h5py.git "$H5PY_SOURCE_PATH" >> "$LOG_FILE" 2>&1
        cd "$H5PY_SOURCE_PATH"
        
        echo "Checking out specific h5py commit..." >> "$LOG_FILE"
        git checkout 102698165a0013c0ebc25d517a606820f2dcdc4d >> "$LOG_FILE" 2>&1
        
        PATCH_FILE_PATH="$SCRIPT_DIR/deps/h5py.patch"
        if [ -f "$PATCH_FILE_PATH" ]; then
            echo "Applying h5py patch..." >> "$LOG_FILE"
            git apply "$PATCH_FILE_PATH" >> "$LOG_FILE" 2>&1
        else
            echo "Error: Patch file $PATCH_FILE_PATH not found. Skipping patch." >> "$LOG_FILE"
            echo -e "${RED}Error: Patch file $PATCH_FILE_PATH not found. Skipping patch application.${NC}" >&2
            # This is a critical step, if patch is missing, we might want to halt or warn severely
            # For now, it will proceed without the patch if not found by fetch_h5py_patch
        fi
        
        echo "Installing patched h5py..." >> "$LOG_FILE"
        HDF5_MPI="ON" CC=mpicc HDF5_DIR="$CONDA_PREFIX" pip install --no-input --no-binary=h5py --no-cache-dir . # Install from current dir (cloned repo)
        echo "h5py installed with MPI support from source within Conda environment."
        cd "$SCRIPT_DIR" # Return to script directory
    } >> "$LOG_FILE" 2>&1
}

# Function to install ephys2 package
install_ephys2() {
    start_step "Installing ephys2 package..."
    {
        conda activate "$CONDA_ENV_NAME"
        rm -rf "$EPHYS_REPO/_skbuild"
        pip uninstall -y ephys2 || true
        pip cache purge
        pip install --no-input -r "$EPHYS_PATH/setup-requirements.txt"
        pip install --no-input -r "$EPHYS_PATH/gui-requirements.txt"
        pip install --no-input -U "$EPHYS_PATH/"
        echo "ephys2 package installed within Conda environment."
    } >> "$LOG_FILE" 2>&1
}

# Function to clean up temporary files and directories
cleanup() {
    start_step "Cleaning up temporary files and directories..."
    rm -rf "$PREFIX" >> "$LOG_FILE" 2>&1
    echo "Temporary files and directories cleaned up."
}

# --- Main Script Execution ---

main() {
    print_msg "Starting installation..."
    choose_install_option
    set_conda_env_name
    setup_temp_folder
    # Fetch the patch before build tools or conda, as it's a dependency for h5py build
    fetch_h5py_patch

    install_build_tools
    install_conda
    initialize_conda_environment
    install_python_packages
    if [ "$INSTALL_OPTION" = "FULL" ]; then
        install_mpi
        install_hdf5
        install_mpi4py
        install_h5py
    fi
    install_ephys2

    cleanup
    print_msg "Installation completed successfully!"
}

# Start the script
main "$@"