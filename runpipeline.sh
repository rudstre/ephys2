#!/bin/bash

mpirun -np $N_PROCS python -m ephys2.run workflow.yaml
