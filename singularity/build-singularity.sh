#!/usr/bin/env bash
set -euo pipefail

dirname="$(basename "$(pwd)")"
if [[ $dirname != 'ephys2' ]]; then
  echo "Run this script from the root directory, not from the ./singularity folder! E.g. ./singularity/build-singularity.sh" >&2
  exit 1
fi

OUTPUT_IMAGE=${1:-"ephys2.sif"}
DEF_FILE=./singularity/mpi.def

singularity build --force "$OUTPUT_IMAGE" "$DEF_FILE"