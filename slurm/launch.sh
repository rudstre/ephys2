#!/bin/bash

#SBATCH --nodes=1																		# Number of nodes
#SBATCH --cpus-per-task=1 													# Number of cpus per task (-c)

# Modules
source $EPHYS2_PATH/slurm/modules.sh
conda activate ephys2

START=$SECONDS

# Run ephys2 with MPI
# srun -n $SLURM_NTASKS --mpi=pmix python -m ephys2.run $CFG
mpirun python -m ephys2.run $CFG

END=$SECONDS
ELAPSED=$((END - START))
echo "Run finished in $ELAPSED seconds."
