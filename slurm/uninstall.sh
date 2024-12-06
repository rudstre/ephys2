#!/bin/bash

#SBATCH --nodes=1																		# Number of nodes
#SBATCH --ntasks-per-node=1     										# Number of tasks per node (-n)
#SBATCH --cpus-per-task=2 													# Number of cpus per task (-c)
#SBATCH -t 0-01:00          												# Runtime in D-HH:MM, minimum of 10 minutes (currently 1 hour)
#SBATCH -p olveczky,test,shared					 						# Partition to submit to
#SBATCH --mem-per-cpu=4000        									# Memory pool for each core 

# Modules
source $EPHYS2_PATH/slurm/modules.sh

# Remove conda environment if exists
if [[ $(conda env list | grep -E "^ephys2\s") ]]; then
    echo "Conda environment 'ephys2' exists. Removing..."
    conda env remove -n ephys2 
else
    echo "Conda environment 'ephys2' does not exist, nothing to remove."
fi
echo "Done."