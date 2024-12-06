# Ephys2 data structures

This document describes the core data structures of `ephys2` (whose implementations may be found in [src/ephys2/lib/types](src/ephys2/lib/types)).

```
Batch
│   Core data structure supporting append/split operations   
│
└───VBatch
│   │   Vector batch, a time-indexed sequence of vectors 
│   │   Example: A sequence of waveforms
│   │
│   └───SBatch
│   │   │   Signal batch, a time-contiguous sequence of vectors with a sampling rate
│   │   │   Example: Amplifier data
│   │
│   └───CVBatch
│   │   │   Compressed vector batch, a time-indexed sequence of vectors with a reverse lookup map into a VBatch
│   │   │   Example: Waveforms which have been compressed
│   │   │
│   │   └───LCVBatch
│   │   │   │   Labeled, linked, & compressed vector batch, a direct combination of CVBatch and LVBatch
│   │   │   │   Example: the output of FAST for a single tetrode
│   │
│   └───LVBatch
│   │       │   Labeled vector batch, a time-indexed sequence of vectors with an integer labeling and an incidence matrix representing a graph of associated labels
│   │       │   Example: Spikes which have been sorted but whose labels have not been finalized yet
│   │
│   └───SBatch
│
└───VMultiBatch
    │   A key-value map of named VBatches 
    │   Example: Sequences of waveforms on multiple tetrodes
    │
    └───CVMultiBatch
    │   │
    │   └───LCVMultiBatch
    │
    └───LVMultiBatch
```

## Example
For example, the FAST pipeline ([examples/fast.yaml](../examples/fast.yaml)) will produce the following datasets during the respective `checkpoint` stages:
```
r4_snippets.h5: VMultiBatch
r4_compressed_snippets.h5: CVMultiBatch
r4_labeled_snippets.h5: LCVMultiBatch
```

## HDF5 outputs

The above data structures are serialized rather directly into HDF5 files. The major deviation from the above structure are the "linkages" or sparse incidence matrices, which are stored as three separate arrays in [Compressed Sparse Row](https://scipy-lectures.org/advanced/scipy_sparse/csr_matrix.html) format.

All serialized data structures in HDF5 have a `tag` attribute which tells you which of the above data structures this HDF5 file represents.

These files can be opened using the HDF5 library in your favorite language:
* Python: [h5py](https://www.h5py.org/)
* MATLAB: [HDF5 library](https://www.mathworks.com/help/matlab/hdf5-files.html)
* R: [hdf5r](https://cran.r-project.org/web/packages/hdf5r/index.html)
* C++: [h5cpp](http://h5cpp.org/)
* Julia: [HDF5.jl](https://juliaio.github.io/HDF5.jl/stable/)

and browsed either manually using the above libraries, or using the built-in HDF loaders in `ephys` (if in Python):

```python
python
>>> import h5py
>>> from ephys2.lib.h5 import *
>>> file = h5py.File('r4_labeled_snippets.h5', 'r')
>>> file.attrs['tag'] # The type of data
'LCVMultiBatch'
>>> data = H5LCVMultiBatchSerializer.load(file, start=None, stop=None) # Pass start/stop to load a subset (e.g. if loading from a remote filesystem)
>>> data['0'].time # Centroid spike times
array([      878,      7383,      7539, ..., 447309391, 447311118,
       447313535])
>>> data['0'].data # Centroid spikes
array([[ 0.65895253,  0.26335993,  2.7923615 , ...,  5.086025  ,
         7.0724564 ,  4.8137746 ],
       [-0.6158093 , -0.9556936 ,  0.45653525, ...,  3.6924012 ,
         3.5592532 ,  2.4022102 ],
       [ 0.27088284, -0.1717158 ,  0.326728  , ...,  1.4647424 ,
         1.4253849 ,  2.1950107 ],
       ...,
       [ 1.378937  ,  0.46425137,  1.6266631 , ...,  4.313972  ,
         2.8979895 ,  3.1215112 ],
       [ 0.83692753,  1.307919  ,  1.2890733 , ...,  5.114403  ,
         4.4455614 ,  5.6124477 ],
       [ 0.22803426,  2.2173736 , -0.5848963 , ..., 17.07054   ,
        18.729786  , 17.191946  ]], dtype=float32)
>>> data['0'].LL.labeling # Spike labels
array([  1,   2,   0, ..., 777, 779, 778])
```


## Visualizing data

You can use the above HDF5 loaders to produce plots for publication in Python (using e.g. `matplotlib` or `seaborn`); meanwhile, for general inspection and exploration, the best approach is to use the ephys2 [GUI](./GUI.md). 

The GUI will automatically detect the data type from the `tag` attribute, and render a type-dependent view.

## Neurodata Without Borders

(Coming soon) This format will be migrated to the [Neurodata Without Borders](https://www.nwb.org/) format, a specification for neurophysiological data built on HDF5.

