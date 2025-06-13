# ephys2 on the Cluster (via Singularity)

## Overview  
We package both the pipeline and GUI of **ephys2** into a single Singularity image (`.sif`) for easy deployment on HPC. A small bash wrapper (`runSingularity.slurm`) lets you invoke any ephys2 command inside that container.

# 1. Using existing singularity builds 

## 1.0 SSH and clone repo

Before you can run anything, you need to ssh into the cluster:
```bash
ssh $(whoami)@login.rc.fas.harvard.edu
```

You then need to clone this repo somewhere on the cluster:
```bash
git clone git@gitlab.com:OlveczkyLab/ephys2.git
```

and then you need to cd into that repo:
```bash
cd ephys2
```

All future commands should be run from this location.

## 1.1 Running the pipeline through singularity

All commands (except [launching the GUI](README.md#12-running-the-gui)) use the same Slurm wrapper:

```bash
sbatch -c <NUM_CORES> \
       --mem=<MEM_MB> \
       -t <TIME_LIMIT> \
       singularity/runSingularity.slurm \
       <OUTPUT_DIR> \
       <COMMAND> \
       [<ARGS…>]
```

- `<COMMAND>` can be:  
  - `run <path/to/config.yaml>` (pipeline)  
  - any other headless bash command  
- Examples:

  ```bash
  # Run spike-sorting pipeline with 8 cores, 500GB memory, with 4hr time limit:
  sbatch -c 8 --mem=500000 -t 04:00:00 \
         singularity/runSingularity.slurm \
         /output/dir \
         run /path/to/config.yaml

  # Custom ephys2 command with 4 cores, 16GB memory, 1hr time limit:
  sbatch -c 4 --mem=16000 -t 01:00:00 \
         singularity/runSingularity.slurm \
         /output/dir \
         "python -m ephys2.customcommand --flag"
  ```
The wrapper will always attempt to send the job to the following partitions (in this order): ***olveczky_sapphire, olveczky, sapphire, shared***. You can override this with a -p flag.

---

## 1.2 Running the GUI  

### 1.2.1 Launch a Remote Desktop  
1. Connect to VPN (if not on ethernet).  
2. Open OnDemand at:  
   https://rcood.rc.fas.harvard.edu  
3. **Select** “Remote Desktop” (not the containerized option), choose resources, and launch.  
4. In the desktop’s terminal:

#### 1.2.2 Run the GUI wrapper  
```bash
./singularity/launchGUI.sh <gui-args>
```

for example:
```bash
./singularity/launchGUI.sh --default-directory /path/to/data
```

if this is your first time running the script, it will install micromamba (if you have no conda setup) and create a new environment called ephys2-gui with the necessary libraries. It will then launch the GUI.

If this is not your first time, it will activate that environment and then run the GUI.

---

## 2. Building New Singularity Images  

If you have made changes to the source code, you will need to compile a new version of the singularity.

**NOTE: You can only compile singularities on Linux!**

### 2.1 Release Builds  
`/n/holylabs/LABS/olveczky_lab/Lab/singularity/releases` is a folder that was created to house all "finalized" versions of the ephys2 source code.

**When runSingularity.slurm is run, it will automatically use the latest release version of the singularity found in this folder.**

If the changes you've made to the source code are intended to be permanent/you are fixing a bug, you should use the following script to build your singularity, and then move it to the above folder when it is complete.

In order to keep track of what source code corresponds to each release version, building a release requires that you are on a git branch that is synced with `main`. The following script will then push a tag to the git repo associating the current commit with the release you are building.

```bash
# From the project root (do NOT cd into singularity/)
./singularity/build-release.sh
```

- Prompts you to commit/push any uncommitted changes  
- Auto‑numbers the new SIF based on existing releases in the release folder. 
- Appends name with unique git commit ID
- Invokes `build-singularity.sh` (≈ 5–10 min)  
- Pushes a tag with the name of your release version to the current git commit you are on.

When this is finished, move the generated SIF to `/n/holylabs/LABS/olveczky_lab/Lab/singularity/releases` either via Globus or some other file transfer service.


### 2.2 Prototype Builds  
If you just want to make a test build and do not plan on moving it to the releases folder, you can run a less constrained version of the build script with no git checks/automatic naming:

```bash
# From the project root
./singularity/build-singularity.sh
```

Wait ~ 5–10 min, and on success, you’ll see:

  ```
  INFO:    Adding environment to container
  INFO:    Adding runscript
  INFO:    Creating SIF file...
  INFO:    Build complete: ephys2.sif
  ```

Rename `ephys2.sif` and upload it to a non-release folder, for example:

  ```bash
  scp ./ephys2_custom.sif $(whoami)@login.rc.fas.harvard.edu:/n/holylabs/LABS/olveczky_lab/Lab/singularity/ephys2-test.sif
  ```

---

