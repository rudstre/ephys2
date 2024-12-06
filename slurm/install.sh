#!/bin/bash

#SBATCH --nodes=1														# Number of nodes
#SBATCH --ntasks-per-node=1     										# Number of tasks per node (-n)
#SBATCH --cpus-per-task=2 												# Number of cpus per task (-c)
#SBATCH -t 0-01:00          											# Runtime in D-HH:MM, minimum of 10 minutes (currently 1 hour)
#SBATCH -p olveczky,sapphire,test,shared					 			# Partition to submit to
#SBATCH --mem-per-cpu=8000        										# Memory pool for each core 

## This slurm installer script mostly mirrors the manual install instructions found in ../ephys2/README_old.sh.
## That doc is the source of truth; please update this script as needed.

START=$SECONDS
echo "Starting build of the current ephys2 branch. Please ensure the version you want is loaded on disk."

# Modules
source $EPHYS2_PATH/slurm/modules.sh

# Create conda environment
# Check if "ephys2" is a currently available conda environment (specifically ephys2 and not any other regexes)
if [[ $(conda env list | grep -E "^ephys2\s") ]]; then
	echo "Conda environment 'ephys2' already exists. Activating..."
else
	# Create a new conda environment called "ephys2" and install the required packages
	echo "Conda environment 'ephys2' does not exist. Creating..."
	conda create -n ephys2 python=3.12.0 -y
fi
conda activate ephys2

# Upgrade pip 
pip install --upgrade pip

# Install build-time dependencies
pip install -r $EPHYS2_PATH/ephys2/setup-requirements.txt 

# Build mpi4py against system mpicc
MPICC=$(which mpicc) pip install --no-binary=mpi4py --no-cache-dir mpi4py

# Build parallel h5py against MPI; $HDF5_HOME is set by the above hdf5 module (use `module show hdf5/1.12.1-fasrc01`)
if [[ -z "$HDF5_HOME" ]]; then
	echo "HDF5_HOME is not set. Exiting..."
	exit 1
fi
# Build h5py from specified commit as in README_old.md
cd $EPHYS2_PATH/..
rm -rf h5py
git clone https://github.com/h5py/h5py
cd h5py
# git checkout 4c01efa9714db40ffe27a322c4f1ba4635816e44
HDF5_MPI="ON" CC=$(which mpicc) HDF5_DIR=$HDF5_HOME pip install -U . --no-build-isolation

# # Install the GUROBI python interface (optional requirement for ephys2); no longer exists on new OS
# pip install gurobipy

# Build Ephys2
cd $EPHYS2_PATH/ephys2
rm -f *.pyc # Remove old build files
rm -rf *.egg-info
rm -rf _skbuild
SITE_PKGS=$(python -c "import site; print(''.join(site.getsitepackages()))")
rm -rf $SITE_PKGS/ephys2* # Remove any existing installation
echo "Removed existing build files. Building ephys2 from source..."
pip install -U . --no-build-isolation # Install source package

# Install optional GUI dependencies
pip install -r $EPHYS2_PATH/ephys2/gui-requirements.txt

# Run tests (TODO: slurm doesn't seem to like the pretty-printing)
# python -m pytest

END=$SECONDS
ELAPSED=$((END - START))
echo "Build finished in $ELAPSED seconds."