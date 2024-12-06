#!/bin/bash

# Preamble for running ephys2-related scripts via slurm
# (Loads common modules)

# Make sure that gcc is the compiler before building mpi4py or ephys2
module load gcc/13.2.0-fasrc01
# module load intel/24.0.1-fasrc01
# OpenMPI module required for parallel HDF5 
module load openmpi/5.0.2-fasrc01 
# Loads parallel HDF5 (gcc / openmpi version); see module spider hdf5
module load hdf5/1.14.3-fasrc01
# Load the GUROBI solver (No longer exists on new OS)
# module load Gurobi/9.1.2 
# Load Python3 Anaconda with h5py
# module load python/3.10.9-fasrc01 
module load Mambaforge/23.11.0-fasrc01

# Load conda into shell
eval "$(conda shell.bash hook)" 