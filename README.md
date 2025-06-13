# Ephys 2.0

**E**lectro**phys**iology spike-sorting pipeline, the **2**nd.

* PI: [Bence Olveczky](https://olveczkylab.oeb.harvard.edu/people/bence-p-olveczky), Professor of Organismic and Evolutionary Biology
* Contact: [Max Shad](mailto:max_shadd@harvard.edu), [Anand Srinivasan](mailto:anand@a0s.co), [Chris Axon](mailto:christopher_axon@harvard.edu), [Rudy Gelb-Bicknell](mailto:rudy.gelb.bicknell@gmail.com)
* Developers: 

    - Mahmood Shad, Associate Director, Research Software Engineering 

    - Anand Srinivasan, Sarah Leinicke and Naeem Khoshnevis, Research Software Engineers


# Getting started 
There are two central components to ephys2: the sorting pipeline and the GUI.

The first main choice point is to decide whether you want to run it on your local computer, or on the cluster. ***Unless you are working with unusually small datasets, the answer is usually the cluster.***

## Running on the cluster

Follow instructions in [singularity/README.md](singularity/README.md)

## Running locally

Follow instructions in [ephys2/README.md](ephys2/README.md)


# General guidelines
These are the user docs; for source code / developer documentation, see the Python package in [ephys2](ephys2).

Follow these steps to use `ephys2`:

1. Write a configuration file; see the [examples/README.md](examples/README.md) for instructions and pre-built configuration files for a variety of different processing pipelines.

2. Install `ephys2` and run your configuration by either following the instructions for cluster ([singularity/README.md](singularity/README.md)) or local installation ([ephys2/README.md](ephys2/README.md)). 

3. Visualize and edit the results. 

4. Use any of the produced datasets in your analysis, by consulting [ephys2/data.md](ephys2/data.md) for documentation of the various HDF5 files produced by `ephys2`. 


# Project organization
* [ephys2](ephys2): Source Python package for Ephys2 
* [scripts](scripts): Utility scripts for ephys2-related workflows
* [docs](docs): Usage & API documentation
* [examples](examples): Example job configuration files
* [singularity](singularity): Singularity build for running on cluster

# Documentation server

[http://199.94.60.144/](http://199.94.60.144/) URL coming soon.

# Resources

The FAST algorithm implemented by `ephys2` is based on the [2017 eLife paper](https://elifesciences.org/articles/27702#fig2s1) - note the [Figures](https://elifesciences.org/articles/27702/figures#fig4s1).



