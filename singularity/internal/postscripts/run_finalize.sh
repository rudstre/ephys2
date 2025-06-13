#!/bin/bash

# Check if input file argument is provided
if [ -z "$1" ]; then
  echo "Error: Input file argument is missing."
  echo "Usage: $0 input_file.h5"
  exit 1
fi

# Create temporary YAML file with variables substituted
INPUT_FILE="$1"
YAML_TEMPLATE="/opt/ephys2/singularity/finalize_pipeline.yaml"
TEMP_YAML="/tmp/finalize_pipeline_temp.yaml"

# Replace $1 with actual input file name
sed "s|\"\$1\"|\"$INPUT_FILE\"|g" "$YAML_TEMPLATE" > "$TEMP_YAML"

# Run the pipeline with the processed YAML
mpirun -np $N_PROCS python -m ephys2.run "$TEMP_YAML"

# Clean up
rm -f "$TEMP_YAML" 