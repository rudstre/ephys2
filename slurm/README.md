# Building & running Ephys2 on the cluster

Building & running on RC consists of 5 steps:
1. Pull the latest source code
2. Set environment variables
3. Submit the build job
4. Submit the run job
5. Monitor your job

If you've done this before, you can skip to steps 3-5.

If you've already built the latest source code, you can skip to steps 4-5.

## 1. Pull the latest source code

Make sure you have SSH keys on cluster linked to your lab Gitlab account. If not, follow the instructions [here](https://gitlab.com/OlveczkyLab/kilosort/-/blob/tetrode/README.md).

Then, clone this repository:
```bash
git clone git@gitlab.com:olveczkylab/ephys2
```

## 2. Set environment variables & load ephys2 commands

Now we'll set some global variables. 

Copy the following into `~/.bashrc`:
```bash
#### Ephys2 ####

# Directory where your ephys2 source package is located
# CHANGE this to wherever you cloned the repository in the last step
export EPHYS2_PATH="/n/holylabs/LABS/olveczky_lab/holylfs02/Anand/ephys2" 

# The default directory where your job files will be written
# CHANGE this to wherever you want to collect your job files
export EPHYS2_JOBS="/n/holylabs/LABS/olveczky_lab/holylfs02/Anand/jobs" 

# Load the ephys2 shell commands
source $EPHYS2_PATH/slurm/commands.sh
```

This setup assumes that the location of your `ephys2` source and the location for job files is static, but you can change them anytime by re-doing the above.

Finally, load the environment variables into your current shell using 
```bash
source ~/.bashrc
``` 
You will have to re-run `source ~/.bashrc` any time the file [commands.sh](commands.sh) is modified.

Finally, check the ephys2 commands available using:
```bash
$ e2 help
Usage: e2 <command> <args>
Commands:
  help
  launch <config> <job_name> {additional_sbatch_parameters}
  launch_debug <config> <job_name> {additional_sbatch_parameters}
  monitor <job_name>
  stdout <job_name>
  stderr <job_name>
  cancel <job_name>
  install
  uninstall
  gui {additional_sbatch_parameters}
  shell
  py {additional_sbatch_parameters}
  squeue
  sacct
```

## 2a. (Optional) Validate your configuration

You can validate your `.yaml` configuration for parameters, as well as determine the estimated memory requirements, using the command:

```python
python -m ephys2.validate MY_CONFIG.yaml
```

* **Running on your local machine**: follow the same steps for installing the GUI in [../ephys2/GUI.md](../ephys2/GUI.md)
* **Running on cluster**: First request an interactive session, then load modules, then run the command. E.g.:
```bash
salloc -p olveczky,shared,test -t 400 -n 1 -c 1 --mem 8000
e2 shell
python -m ephys2.validate MY_CONFIG.yaml
```

## 3. Build

(Optional: check whether you have the latest source by pulling from master, `git pull origin master`.)

(If doing a fresh install: run `e2 uninstall` first and wait for the job to complete.)

Submit the build job:
```bash
e2 install
```
(you can change any parameters, such as the job name, in the above script.)

Monitor the build using:
```bash
e2 monitor install
```

## 4. Run

Submit the run job using (make sure not to run this from within an existing interactive job, or the environment variables could conflict):
```bash
e2 launch my_config.yaml job_name
```
Job files will be written to `$EPHYS2_JOBS/my_job.out` and `$EPHYS2_JOBS/my_job.err`. Jobs are listed in `squeue` or `sacct` with `e2_` prepended.

### (Optional) Run manually within an interactive job

Follow these steps to run `ephys2` manually on the cluster.
* First request an interactive job:
```bash
salloc -p olveczky,shared,test -t 400 -n 1 -c NUM_CORES --mem 16000 # Request more cores / mem if you wish
```
* Then load the `ephys2` dependencies:
```bash
e2 shell
```
(Alternatively, just to load the necessary modules, you can run:)
```bash
source $EPHYS2_PATH/slurm/modules.sh
```
* Finally run `ephys2` using:
```bash
srun -n NUM_CORES --mpi=pmix python -m ephys2.run MY_CONFIG.YAML # Ensure NUM_CORES matches
```

**Changing the default slurm parameters**: your jobs will run by default with 32 workers and 3.5GB memory per worker. If you want to change this (for example, submitting a job with larger memory requirements) simply pass additional parameters as you would to `sbatch`:

```bash
# Example submission of high-memory job
e2 launch my_config.yaml job_name --partition bigmem --mem 320000

# Example submission of long-running job (1 day)
e2 launch my_config.yaml job_name --partition shared --time 1-00:00 

# Example submission of low-footprint job
e2 launch my_config.yaml job_name --ntasks-per-node 2 --mem 7000
```

In general, the relevant `sbatch` parameters are:
```bash
--partition # Partition on RC, https://docs.rc.fas.harvard.edu/kb/running-jobs/
--ntasks-per-node # Number of parallel workers; for now, ephys2 uses only 1 node
--mem # Total memory size in MB (will be divided among # workers)
--time # Time limit in D-HH:MM
```

All data will be read from and written to the filepaths specified in your configuration file. **Any filepaths you specified as outputs in your configuration file will be overwritten, if they already exist (e.g. from previous runs); change paths over multiple runs as necessary.** 

Input data files are not modified; `ephys2` can be terminated at any time.

(**Note**: to run with debug statements and profiling enabled, which can be helpful for diagnosing issues, use the above commands with `e2_debug` instead.)

## 5. Monitor your job

* Check the status of your job using `squeue`, where your job should appear momentarily after submission. 
* Check your job's position in the queue using `sacct`.
* For convenience, filter the output of `squeue` or `sacct` to only show `ephys2` jobs using:
```bash
e2 squeue
e2 sacct
```

e.g.:
```bash
[asrini@holy7c02409 ephys2]$ e2 sacct
13710542     e2_install       test   rc_admin          2  COMPLETED      0:0
```

* Once your job appears in `squeue`, you can check its status using `scontrol show job $JOB_ID` where `$JOB_ID` is the integer ID found using `squeue`. If allocation takes a long time, try changing the partition using the `--partition` argument as above. 

* Watch both `stdout` and `stderr` simultaneously using:
```bash
e2 monitor job_name
```

* Watch `stdout` and `stderr` separately using:
```bash
e2 stdout job_name
e2 stderr job_name
```
The `stdout` and `stderr` files are located in `EPHYS2_JOBS` (`cd $EPHYS2_JOBS`). To cancel a running job using its name (assuming the name is unique in `squeue`), do:
```bash
e2 cancel job_name
```

## 6. Using the GUI 

### Option 1: Transfer data locally, in whole or part

If the entire `.hdf5` file will fit in your workstation disk, then a good option is to simply transfer the file locally using [Globus](https://www.globus.org/).

However, often your data will not fit entirely on disk. In this case, `ephys2` provides a command-line tool to export & import specific channel groups (e.g., tetrodes) into a smaller `.hdf5` file, which you can transfer locally and then merge back in to your original dataset on the cluster after your changes.

0. **Get an interactive session using `e2 shell`.**
* Make sure you have loaded the above commands ^ into your `~/.bashrc` and you have `source ~/.bashrc`.
* Request an interactive job, e.g. using 
```bash
salloc -p olveczky,shared,test -t 100 -n 1 -c 4 --mem 16000
```
* Load the required modules using 
```bash
e2 shell
```

1. **Export channel groups.** Run 
```bash
# Export channel groups 0, 2, 5 from LARGE_FILE.hdf5 into SMALL_FILE.hdf5
python -m ephys2.copy_channel_groups -i LARGE_FILE.hdf5 -o SMALL_FILE.hdf5 -g 0,2,5 
```
Then you can transfer this data to your workstation using any method.

2. **Import updated channel groups.** Once you've finished editing `SMALL_FILE.hdf5`, upload it back to the cluster and run the same command in the reverse direction.
```bash
# Overwrite channel groups 0, 2, 5 in the original dataset using the edited one
python -m ephys2.copy_channel_groups -i SMALL_FILE.hdf5 -o LARGE_FILE.hdf5 -g 0,2,5
```
Note that this can increase the size of your original file, since HDF5 doesn't do replacements in-place. If you wish to re-pack your data to claim deleted space, pass `-r` to the above command.

To see the use instructions at any time, simply ask for help:
```bash
python -m ephys2.copy_channel_groups -h
```

### Option 2: Run GUI on the cluster with X11 forwarding
This section will show you how to run the GUI as a compute job. The benefit is that no data copying is required over the network, but the downside is it can be very slow to interact with / render, depending on your connection latency.

1. First, ensure you have an `X server` installed. 
* If on Linux, you already have it.
* If on macOS, install [XQuartz](https://www.xquartz.org/)
* If on Windows, install [Xming](https://sourceforge.net/projects/xming/) or [Cygwin](https://www.cygwin.com/) (see, for example, [these Cygwin instructions on Windows](https://cs.hofstra.edu/docs/pages/guides/cygwin_x11_forwarding.html))

Make sure to start the X server before proceeding to the next step.

2. Login to the FAS RC cluster using `ssh -CY USER@login.rc.fas.harvard.edu`. `-Y` enables display forwarding, and `-C` enables compression.

3. Ensure your RC bash profile contains the above commands.

4. Navigate to your data folder of choice, and run `e2 gui`. This starts a graphical interactive job on the [remoteviz](https://docs.rc.fas.harvard.edu/kb/running-jobs/) partition, which contains GPUs for rendering. You can pass any other parameters as you would to a slurm interactive job, such as 
```bash
e2 gui --mem 32000 # Request 32GB instead of 16GB ram
```
Wait a few moments, and the `ephys2` GUI window should pop up on your machine.

## 7. Inspect your data on the cluster

Ensure you have the above commands loaded in your `~/.bashrc`, and then run:
```bash
e2 py
```
Just as in `e2 gui`, you can pass any relevant `slurm` parameters here. e.g.:
```bashrc
e2 py --mem 32000
```
You can then open your data using 
```bash
Python 3.9.7
>>> from ephys2.lib.h5 import *
>>> f = h5py.File('my_file.h5', 'r') # Do not pass 'w', it will delete your file!
>>> f.keys()
<KeysViewHDF5 ['0', '1', '10', '11', '12', '13', '14', '15', '2', '3', '4', '5', '6', '7', '8', '9']>
```
From here you can import various libraries, export your data into various formats, do analysis, etc. `ephys2` exposes several utility functions; for example, you can find the indices closest to a specific point in time:
```bash
>>> tetr0 = f['0']
>>> tetr0.keys()
<KeysViewHDF5 ['data', 'excluded_units', 'labels', 'linkage', 'summary', 'time']>
>>> query_sample = 1100 * 60 * 60 * 30000 # Find out what's going on at 1100h
>>> idx0, idx1 = binary_search_interval(tetr0['time'], query_sample)
>>> idx0, idx1 # Closest matching indices to your requested time
(57048901, 57048902)
>>> tetr0['data'][idx0] # Load the waveform at this index
array([ 3.10632515e+00,  2.53102055e+01,  5.28278503e+01,  7.48544464e+01, ...
```

**Note:** this environment is fully MPI-enabled, although the Python interpreter itself here is a single process.

### Handling failures
`ephys2` will parse your pipeline and exit with errors if any are found, before running any computations. Check for any using `cat $EPHYS2_JOBS/my_job.err`. Generally, these errors will be self-explanatory, but here are some examples:

* `TypeError`: 
	* you attempted to chain two incompatible steps, such as running a bandpass filter on snippeted data
	* you provided a parameter of the wrong type
* `ValueError`: 
	* you provided a parameter outside the expected range or failed to provide the parameter
	* you provided a file or directory path which doesn't exist or you don't have permissions to read/write
	* you selected a processing stage which doesn't exist

No computations are destructive, so in the event of a failure simply delete any files created by `ephys2` and re-run your job with the correct settings.

While running, `ephys2` may create temporary directories (`tmp_ephys2_NODELETE_...`); deleting or modifying these during runtime will cause a crash. These will be automatically deleted upon successful completion.
If you encounter a crash, and they remain, you can safely delete them.

# TODO (developer) 
* estimate memory requirements from batch sizes, warn if batch size too high
* estimate time requirements from data size, warn if too low