#!/bin/bash -e

dirname=`basename $(pwd)`

if [[ $dirname != 'ephys2' ]]; then
    echo "Run this script from the root directory, not from the ./singularity folder! E.g. ./singularity/build-singularity.sh"
    exit 1
fi

sudo singularity build --force ephys2.sif ./singularity/mpi.def
