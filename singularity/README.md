# ephys2 on the Cluster (via Singularity)

## Overview  
We package both the pipeline and GUI of **ephys2** into a single Singularity image (`.sif`) for easy deployment on HPC. A small bash wrapper (`runSingularity.slurm`) lets you invoke any ephys2 command inside that container.

---

## 1. Building Singularity Images  

### 1.1 Release Builds  
Use this when you’ve finalized code on a git branch that’s synced with `main`.

```bash
# From the project root (do NOT cd into singularity/)
./singularity/build-release.sh
```

- Prompts you to commit/push any uncommitted changes  
- Auto‑numbers the new SIF based on existing releases in  
  `/n/holylabs/LABS/olveczky_lab/Lab/singularity/releases`  
- Appends name with unique git commit ID
- Invokes `build-singularity.sh` (≈ 5–10 min)  
- Move the generated SIF to the releases folder (e.g., via Globus)

### 1.2 Prototype Builds  
Quick iteration on cluster changes—no git checks:

```bash
# From the project root
./singularity/build-singularity.sh
```

- Wait ~ 5–10 min  
- On success, you’ll see:

  ```
  INFO:    Adding environment to container
  INFO:    Adding runscript
  INFO:    Creating SIF file...
  INFO:    Build complete: ephys2.sif
  ```

- Rename `ephys2.sif` and upload it, for example:

  ```bash
  scp ./ephys2_custom.sif $(whoami)@login.rc.fas.harvard.edu:/n/holylabs/LABS/olveczky_lab/Lab/singularity/ephys2-a.sif
  ```

---

## 2. Running ephys2 commands through singularity  

All commands use the same Slurm wrapper:

```bash
sbatch -c <NUM_CORES> \
       --mem=<MEM_MB> \
       -t <TIME_LIMIT> \
       runSingularity.slurm \
       <OUTPUT_DIR> \
       <COMMAND> \
       [<ARGS…>]
```

- `<COMMAND>` can be:  
  - `run <path/to/config.yaml>` (pipeline)  
  - any other headless bash command  
- Examples:

  ```bash
  # Run spike-sorting pipeline with 64 cores, 500GB memory, with 4hr time limit:
  sbatch -c 8 --mem=500000 -t 04:00:00 \
         runSingularity.slurm \
         /output/dir \
         run /path/to/config.yaml

  # Custom ephys2 command with 4 cores, 16GB memory, 1hr time limit:
  sbatch -c 4 --mem=16000 -t 01:00:00 \
         runSingularity.slurm \
         /output/dir \
         "python -m ephys2.customcommand --flag"
  ```
The wrapper will always attempt to send the job to the following partitions (in this order): ***olveczky_sapphire, olveczky, sapphire, shared***. You can override this with a -p flag.

---

## 3. Running the GUI  

### 3.1 Launch a Remote Desktop  
1. Connect to VPN (if not on ethernet).  
2. Open OnDemand at:  
   https://rcood.rc.fas.harvard.edu  
3. **Select** “Remote Desktop” (not the containerized option), choose resources, and launch.  
4. In the desktop’s terminal:

#### 3.2 First‑Time Setup  
```bash
# Install Micromamba
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)

# Initialize and restart your shell
micromamba init
exec $SHELL

# Create GUI environment
micromamba create -n ephys2-gui xcb-util-cursor
```

#### 3.3 Run the GUI  
```bash
# Activate GUI env
micromamba activate ephys2-gui

# Launch ephys2 GUI
singularity run --bind /n /path/to/ephys2.sif gui

# OR Lanuch ephys2 GUI with particular default directory
singularity run --bind /n /path/to/ephys2.sif gui --default-directory /path/to/data/dir
```
**Note:** The `--bind /n` flag ensures cluster file systems are accessible within the singularity. 

If you just need the latest version of the gui with no modifications, I'd recommend going with the latest release within ***/n/holylabs/LABS/olveczky_lab/Lab/singularity/releases***

---