#!/bin/bash
#SBATCH -J runSingularity
#SBATCH -p olveczky_sapphire,olveczky,sapphire,shared
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# Require at least SCRIPT_PATH and OUTPUT_PATH
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <SCRIPT_PATH> <OUTPUT_PATH> [additional args...]" >&2
  exit 1
fi

# Pull off the mandatory arguments
OUTPUT_PATH=$1
SCRIPT_PATH=$2
shift 2

# Make sure output directory exists
mkdir -p "$OUTPUT_PATH"

# Make your script executable if it exists
if [[ -e "$SCRIPT_PATH" ]]; then
  chmod +x "$SCRIPT_PATH"
else
  echo "Warning: script '$SCRIPT_PATH' not found" >&2
fi

echo "Running: $SCRIPT_PATH"
echo "N_PROCS = ${SLURM_CPUS_PER_TASK:-1}"

# --- DYNAMIC SIF LOOKUP ---
RELEASE_DIR="/n/holylabs-olveczky/Lab/singularity/releases"

# Option A: version-sort by filename (requires GNU sort -V)
latest_sif=$(ls -1 "${RELEASE_DIR}"/ephys2-release-*.sif 2>/dev/null \
             | sort -V \
             | tail -n1)

if [[ -z "$latest_sif" ]]; then
  echo "Error: no Singularity images matching '${RELEASE_DIR}/ephys2-release-*.sif' found" >&2
  exit 1
fi

echo "Using Singularity image: $latest_sif"

# Run it
singularity run \
  --env N_PROCS="$SLURM_CPUS_PER_TASK" \
  --cleanenv \
  --bind /n,"$OUTPUT_PATH":/outputs \
  "$latest_sif" \
  "$SCRIPT_PATH" "$@"