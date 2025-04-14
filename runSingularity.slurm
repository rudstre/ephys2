#!/bin/bash
#SBATCH -J runSingularity        # job name
#SBATCH -o runSingularity.out    # standard output file
#SBATCH -e runSingularity.err    # standard error file
#SBATCH -p olveczky_sapphire,olveczky,sapphire,shared,test

SCRIPT_PATH=$1
chmod +x "$SCRIPT_PATH"
echo "Running $SCRIPT_PATH."
echo "N_PROCS = $SLURM_CPUS_PER_TASK"
singularity run --env N_PROCS=$SLURM_CPUS_PER_TASK --cleanenv \
  --bind /n \
  /n/holylabs/LABS/olveczky_lab/Lab/singularity/ephys2.sif "$SCRIPT_PATH"
