# Ephys 2.0

**E**lectro**phys**iology spike-sorting pipeline, the **2**nd.

* PI: [Bence Olveczky](https://olveczkylab.oeb.harvard.edu/people/bence-p-olveczky), Professor of Organismic and Evolutionary Biology
* Contact: [Max Shad](mailto:max_shadd@harvard.edu), [Anand Srinivasan](mailto:asrinivasan@g.harvard.edu), [Sarah Leinicke](mailto:sarahleinicke@g.harvard.edu), [Naeem Khoshnevis](mailto:naeemkhoshnevis@g.harvard.edu), [Chris Axon](mailto:christopher_axon@harvard.edu) (current RSE at Olveczky Lab)
* Developers: 

    - Mahmood Shad, Associate Director, Research Software Engineering 

    - Anand Srinivasan, Sarah Leinicke and Naeem Khoshnevis, Research Software Engineers

# Running on cluster (singularity)

`singularity run --env N_PROCS=4 --cleanenv /n/holylabs/LABS/olveczky_lab/Lab/singularity/ephys2.sif ~/caxon_lustre/ephys_test_config.yaml`

NOTES:
* make sure you run from within a sbatch script! *NOT ON LOGIN NODES!*
* replace `N_PROCS=4` with number of tasks from slurm sbatch
* the final argument should point to your config yaml script
* `--cleanenv` is very important! Without this argument, the container will only use 1x core isntead of `N_PROCS` CPU cores.
* if you have any questions about running singularity, ask Chris Axon

# Getting started 

These are the user docs; for source code / developer documentation, see the Python package in [ephys2](ephys2).

Follow these steps to use `ephys2`:

1. Write a configuration file; see the [examples/](examples) for instructions and pre-built configuration files for a variety of different processing pipelines.

2. Install `ephys2` and run your configuration by either following the instructions for slurm submission ([slurm/README.md](slurm/README.md)) or local installation ([ephys2/README.md](ephys2/README.md)). 

3. Visualize and edit the results, following the instructions in [ephys2/GUI.md](ephys2/GUI.md). 

4. Use any of the produced datasets in your analysis, by consulting [ephys2/data.md](ephys2/data.md) for documentation of the various HDF5 files produced by `ephys2`. 

# FAQ

**How do I run the pipeline on RC?**

See the "Running on cluster (singularity)" section

**How do I run the pipeline on my local machine?**

Follow the developer build instructions in [ephys2/README.md](ephys2/README.md).

**How do I run the GUI on my local machine?**

Follow the instructions in [ephys2/GUI.md](ephys2/GUI.md)

**I ran into an error.**

If the error is with your configuration file, check the [Handling failures](slurm/README.md#handling-failures) section in the [RC doc](slurm/README.md). Otherwise, open an [issue](https://gitlab.com/OlveczkyLab/ephys2/-/issues).


# Project organization
* [ephys2](ephys2): Source Python package for Ephys2 
* [scripts](scripts): Utility scripts for ephys2-related workflows
* [docs](docs): Usage & API documentation
* [examples](examples): Example job configuration files
* [slurm](slurm): Slurm build & run batch jobs

# Documentation server

[http://199.94.60.144/](http://199.94.60.144/) URL coming soon.

# Resources

The FAST algorithm implemented by `ephys2` is based on the [2017 eLife paper](https://elifesciences.org/articles/27702#fig2s1) - note the [Figures](https://elifesciences.org/articles/27702/figures#fig4s1).



