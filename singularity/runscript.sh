#!/bin/bash

echo "Running ephys2 [singularity]"
echo "N_PROCS IS $N_PROCS"

mpirun -np $N_PROCS python -m ephys2.run $1
