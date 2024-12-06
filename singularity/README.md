# Building ephys2 singularity cluster

Build tested on a Linux Workstation. 64GB RAM, i7-14700K (28 core), RTX 4080 GPU (not used for build).

Run the following command from the root git project directory (likely `ephys2`). i.e. do NOT `cd singularity` first!

```bash
./singularity/build-singularity.sh
```

This will take about 5-10 minutes.

If the build is successful, the terminal output should say: 

```
INFO:    Adding environment to container
INFO:    Adding runscript
INFO:    Creating SIF file...
INFO:    Build complete: ephys2.sif
```

and there should be a file called ephys2.sif in the root directory (about 2GB).

Upload this file to the cluster:

```
scp ./ephys2.sif `whoami`@login.rc.fas.harvard.edu:/n/holylabs/LABS/olveczky_lab/Lab/singularity/ephys2-a.sif
```


## How to run singularity on the cluster?

update the command with `/path/to/ephys2/yaml/file` set to the full path to your yaml config file on the cluster.

update N_PROCS=4 to the number of cores you want to use on the cluster. Make sure this number does not excede the # of cores on the node (as this build does not support multi-node MPI).

`singularity run --env N_PROCS=4 --cleanenv /n/holylabs/LABS/olveczky_lab/Lab/singularity/ephys2.sif /path/to/ephys2/yaml/file`

