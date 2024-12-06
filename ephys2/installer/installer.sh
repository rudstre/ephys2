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
source "${SCRIPT_DIR}/aux/envvars.sh"

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
}

# Function to install build tools
install_build_tools() {
    start_step "Installing build tools..."
    if $MACOS; then
        if [ -d "/Applications/CMake.app" ]; then
            echo "CMake.app already exists in /Applications."
        else
            {
                curl -L -o "${CMAKE_SOURCE_PATH}.tar.gz" "$CMAKE_DOWNLOAD_URL"
                mkdir -p "$CMAKE_SOURCE_PATH"
                tar -xzf "${CMAKE_SOURCE_PATH}.tar.gz" -C "$CMAKE_SOURCE_PATH" --strip-components 1
                sudo mv "$CMAKE_SOURCE_PATH/CMake.app" /Applications/
                echo "CMake.app installed in /Applications."
            } >> "$LOG_FILE" 2>&1
        fi
    else
        {
            sudo apt update
            sudo apt install -y build-essential wget
            echo "build-essential and wget installed via apt."
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
                conda init --reverse
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
    start_step "Initializing Conda environment..."
    source "$CONDA_PATH/etc/profile.d/mamba.sh"
    mamba init "$SHELL_NAME"
    mamba activate base
    if mamba info --envs | grep -q "$CONDA_ENV_NAME"; then
        echo "Conda environment '$CONDA_ENV_NAME' already exists."
        read -rp "What would you like to call the Conda environment instead? " CONDA_ENV_NAME
    fi
    {
        mamba create -n "$CONDA_ENV_NAME" python="$PYTHON_VERSION" -y
    } >> "$LOG_FILE" 2>&1
    echo "Conda environment '$CONDA_ENV_NAME' created."
    mamba activate "$CONDA_ENV_NAME"
}

# Function to install Python packages
install_python_packages() {
    start_step "Installing Python packages..."
    mamba activate "$CONDA_ENV_NAME"
    if [ "$INSTALL_OPTION" = "GUI" ]; then
        {
            mamba install -c conda-forge numpy scipy matplotlib osqp cvxopt cython mpi4py -y
        } >> "$LOG_FILE" 2>&1
        echo "Python packages installed via Conda."
    elif [ "$INSTALL_OPTION" = "FULL" ]; then
        {
            pip install --no-input numpy scipy matplotlib osqp cvxopt cython
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
        mamba activate "$CONDA_ENV_NAME"
        pip uninstall -y mpi4py || true
        pip cache purge
        export PATH="$CONDA_PREFIX/bin:$PATH"
        MPICC=$(which mpicc) pip install --no-binary=mpi4py --no-cache-dir mpi4py
        echo "mpi4py installed within Conda environment."
    } >> "$LOG_FILE" 2>&1
}

# Function to install h5py
install_h5py() {
    start_step "Installing h5py with MPI support within Conda environment..."
    {
        mamba activate "$CONDA_ENV_NAME"
        pip uninstall -y h5py || true
        pip cache purge
        HDF5_MPI="ON" CC=mpicc HDF5_DIR="$CONDA_PREFIX" pip install --no-input --no-binary=h5py --no-cache-dir h5py
        echo "h5py installed with MPI support within Conda environment."
    } >> "$LOG_FILE" 2>&1
}

# Function to install ephys2 package
install_ephys2() {
    start_step "Installing ephys2 package..."
    {
        mamba activate "$CONDA_ENV_NAME"
        rm -rf "$EPHYS_REPO/_skbuild"
        pip uninstall -y ephys2 || true
        pip cache purge
        pip install --no-input -r "$EPHYS_PATH/setup-requirements.txt"
        pip install --no-input -r "$EPHYS_PATH/gui-requirements.txt"
        pip install --no-input -U "$EPHYS_PATH/"
        echo "ephys2 package installed within Conda environment."
    } >> "$LOG_FILE" 2>&1
}

# Function to create Conda activation and deactivation scripts
create_conda_activation_scripts() {
    start_step "Installing Conda activation and deactivation scripts..."
    {
        ACTIVATE_DIR="$CONDA_PREFIX/etc/conda/activate.d"
        DEACTIVATE_DIR="$CONDA_PREFIX/etc/conda/deactivate.d"

        mkdir -p "$ACTIVATE_DIR"
        mkdir -p "$DEACTIVATE_DIR"

        # Determine which activation script to use based on the installation option
        if [ "$INSTALL_OPTION" = "FULL" ]; then
            ACTIVATE_SCRIPT="conda/activate_ephys2_full.sh"
        else
            ACTIVATE_SCRIPT="conda/activate_ephys2_gui.sh"
        fi

        # Copy the activation and deactivation scripts from the repository
        cp "$SCRIPT_DIR/$ACTIVATE_SCRIPT" "$ACTIVATE_DIR/activate_ephys2.sh"
        cp "$SCRIPT_DIR/conda/deactivate_ephys2.sh" "$DEACTIVATE_DIR/"

        # Ensure the scripts are executable
        chmod +x "$ACTIVATE_DIR/activate_ephys2.sh"
        chmod +x "$DEACTIVATE_DIR/deactivate_ephys2.sh"

        echo "Conda activation and deactivation scripts installed."
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
    install_build_tools
    install_conda
    source "$CONDA_PATH/etc/profile.d/conda.sh"
    initialize_conda_environment
    install_python_packages
    if [ "$INSTALL_OPTION" = "FULL" ]; then
        install_mpi
        install_hdf5
        install_mpi4py
        install_h5py
    fi
    install_ephys2
    create_conda_activation_scripts

    cleanup
    print_msg "Installation completed successfully!"

    # Inform the user about the alias
    print_msg "You can now run the GUI using the command 'ephys2gui' in the activated conda environment."
}

# Start the script
main "$@"