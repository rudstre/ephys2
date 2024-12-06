# Ephys2 GUI

**Note**: do not open the GUI on an `HDF5` file which is currently being written to by a job - it could cause your job to crash.

**Note**: if you have a modern Mac, ensure you disable dark mode (`System Preferences > General > Appearance > Light`) before opening the GUI.

## Installing the GUI on your local machine

### Automated install script

#### 1. Clone Ephys2 Repo

Clone repo according to the [ephys2 local install instructions](./README.md) (step 1).

#### 2. Run the ephys installer
In the command-line, cd to the installer folder of your newly cloned repo:

```bash
cd ephys2/ephys2/installer
```

and then run the following command:
```bash
bash installer.sh
```

Give the script your computer password, **select the gui-only install**, select the desired conda preference, and the rest will be done automatically.

### Docker

See [the Docker README](../docker/README.md).

### Manual install (not recommended)

First, create a new `conda` environment for `ephys2`, if you haven't done so already:
```bash
conda create -n ephys2 python=3.10
conda activate ephys2
```

1. (Optional, if you're on an M1 mac):

Install the following dependencies first:

```bash
conda install -c conda-forge numpy scipy matplotlib osqp cvxopt cython mpi4py
````

2. Install the GUI:

Then clone this repository to your local machine, and install the project and additional GUI dependencies using:
```bash
git clone git@gitlab.com:olveczkylab/ephys2
cd ephys2/ephys2
pip install -r setup-requirements.txt
pip install -r gui-requirements.txt # Install additional GUI requirements
```
(If you're on Windows, ensure to run `rm -rf _skbuild` before the next step. Currently, this needs to be done every time you update the GUI.)
```bash
pip install -U .
```

Note: if the `PyQT6` install fails or isn't available for your system, you can alternatively install `PySide6`.

## Using the GUI

### Browsing data
You can use the GUI to browse any HDF5 dataset created during a `checkpoint` stage of your pipeline, such as:
```yaml
- checkpoint:
	  directory: /Users/anandsrinivasan/dev/fasrc/data # Directory containing output data
	  name: r4_snippets.h5 # Snippets are stored as a single HDF5 file
	  batch_size: 1000 # Batch size determines chunking for next stage
	  batch_overlap: 0
```

Either copy this dataset to your local machine or mount the remote filesystem (e.g. using Samba). The GUI will only load whatever you're viewing, so you won't be loading the whole dataset.

Then, run: 
```bash
ephys2gui
``` 
from any location. From the main window, press `Ctrl+O`/`Cmd+O`/`File... Open` and open any ephys2 HDF5 file. 

For instance, opening a file checkpointed following the `label.spc_segfuse` stage shows the following:

![](../docserver/images/labeled.png)

Use the arrow keys to navigate, and `Ctrl +` / `Cmd +` / `Ctrl -` / `Cmd -` to zoom in or out. To view an individual waveform, click on the datapoint. 

Notice that if you ran a compression step (e.g. `compress.spc`) prior to the labeling, a `Link to raw data` button will appear at the bottom. Clicking it will open a file picker, and you can open the corresponding file produced earlier in your pipeline corresponding to the raw snippets. (Opening any other file will produce errors.) 

Clicking on any datapoint in the view will open a new window with the raw datapoints which have been compressed:

![](../docserver/images/raw_linked.png)

If you open a "labeled" dataset (see [data.md](data.md)), you can additionally toggle the links:

![](../docserver/images/links.gif)

You can also explore raw data; for example, running [../examples/crcns_hc1_raw.yaml](../examples/crcns_hc1_raw.yaml), we can open `hc1_signals.h5` to see both extracellular and intracellular recordings from that dataset:

![](../docserver/images/hc1_raw.png)

Then, if we select only the extracellular channels and apply a bandpass filter as in [../examples/crcns_hc1.yaml](../examples/crcns_hc1.yaml):

![](../docserver/images/hc1.png)

You can also load other raw files, such as `.rhd` or Intan one-file-per-signal-type:

![](../docserver/images/load_raw.gif)

### Editing data 

#### Merging links:

Click on one unit, then Shift+Click to bring up the Cross-Correlogram. In this view you can click "merge units":

![](../docserver/images/merging.gif)

## Running the GUI on cluster

For very large data, you may find that loading data over a network drive or copying data locally is infeasible. In such cases, you can run the GUI as a compute job on the computing cluster with X11 forwarding enabled. See [../slurm/README.md](../slurm/README.md) for instructions.

**Note: NO LONGER WORK AS X11 FORWARDING HAS BEEN DEPRECATED ON CLUSTER**
## Use on VDI (coming soon)