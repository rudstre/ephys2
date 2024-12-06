# Example Ephys2 workflows

To get started, copy one of the files in this directory and start modifying the parameters. Make sure the filepaths point to your data. We recommend using absolute filepaths always (use the `pwd` command in a directory).

## Examples
* [snippet.yaml](snippet.yaml): Snippet a standard RHD2000 file.
* [snippet_ofps.yaml](snippet_ofps.yaml): Snippet an Intan "one file per signal type" directory.
* [snippet_multi.yaml](snippet_multi.yaml): Snippet multiple RHD2000 files, explicitly specified.
* [snippet_multi_pattern.yaml](snippet_multi_pattern.yaml): Snippet multiple RHD2000 files, specified using a wildcard `*` pattern.
* [label.yaml](label.yaml): Label a previously snippetted (and possibly compressed) dataset (e.g. results of `snippet.yaml` or `snippet_and_compress.yaml`).
* [snippet_and_label.yaml](snippet_and_label.yaml) Snippet and label an RHD2000 file, without an intermediate compression step (suitable for short-term recordings).
* [fast.yaml](fast.yaml) Run the entire FAST algorithm on an RHD2000 file.
* [fast_rhd64.yaml](fast_rhd64.yaml) Run the entire FAST algorithm on an RHD file in the FAST 64-channel RHD format.
* [fast_mearec.yaml](fast_mearec.yaml) Run the FAST algorithm on a MEArec (Neuron)-generated synthetic spike dataset.
* [spc_dhawale.yaml](fast_dhawale.yaml) Run the FAST algorithm on the [Zenodo synthetic spike dataset](https://zenodo.org/record/886516#.YiFMg1jML0o).
* [crcns_hc1.yaml](crcns_hc1.yaml) Download & process a recording from the [CRCNS-HC1 dataset](https://crcns.org/data-sets/hc/hc-1/about).
* [isosplit_manual.yaml](fast_isosplit_manual.yaml) Run the FAST algorithm using ISO-SPLIT for the clustering step, with a manual curation step
* [isosplit_manual_onefile.yaml](fast_isosplit_manual_onefile.yaml) Like the previous, but uses pass-through serialization to write everything to a single file (for large jobs, this will generally be a lot faster, about 1.5-3x)
* [isosplit_auto.yaml](fast_isosplit_auto.yaml) Run the FAST algorithm using ISO-SPLIT for the clustering step, without a manual curation step
* [mr_isosplit_benchmark.yaml](mr_isosplit_benchmark.yaml) Example using ISO-SPLIT with the segmentation fusion step on synthetic spike data
* [finalize.yaml](finalize.yaml) Finalize the links into labels after editing the clustering using the GUI. (isosplit)
* [postprocess_label.yaml](postprocess_label.yaml) Use an XGBoost classifier to auto-label noise clusters (for use in GUI)
* [postprocess_filter.yaml](postprocess_filter.yaml) Same as above, but this one explicitly filters the noise clusters.
* [label_multi.yaml](label_multi.yaml) Run the labeling step across multiple input snippets files, with automatic re-offsetting of the time index based on start times contained in the files
* [resummarize.yaml](resummarize.yaml) Re-compute the summarization for a dataset (necessary, for example, if you split clusters in the detailed view, or if you want to downsample data at a different rate)
* [relabel.yaml](relabel.yaml) Re-run the labeling step for a dataset in-place (for example to try different clustering parameters)

## Write your own

`ephys2` pipelines are specified using [YAML](https://lzone.de/cheat-sheet/YAML) configuration files. Here's an example (taken from the latest pipeline, [isosplit_link.yaml](isosplit_link.yaml)):

(**Important**: when specifying session names with a date pattern match, consult [https://strftime.org](https://strftime.org) for the correct codes.)

```yaml
# Link & label using ISO-SPLIT
# ============================

- input.rhd2000:
    sessions: /n/holylfs02/LABS/olveczky_lab/Anand/data/r4_210612_195804.rhd # Path to RHD file
    datetime_pattern: "*_%y%m%d_%H%M%S" # Pattern to extract timestamps from the filenames (ensure to put in double-quotes; simply pass "*" to ignore patterns) - this ensures a consistent sample index across multiple files
    batch_size: 450000 # Processing batch size 
    batch_overlap: 0 
    aux_channels: []

- preprocess.bandpass:
    order: 4 # Filter order (increase to obtain better filter response, at the expense of performance and numerical stability)
    highpass: 300 # Highpass filter frequency (Hz)
    lowpass: 7500 # Lowpass filter frequency (Hz)
    Rp: 0.2 # Maximum ripple in the passband (dB)
    Rs: 100 # Minimum attenuation in the stopband (dB)
    type: ellip # Filter type (options: `ellip`, `cheby1`, `cheby2`), see https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.iirdesign.html
    padding_type: odd # Signal extension method (others supported: `odd`, `even`)
    padding_length: 1000 # Edge padding

- preprocess.median_filter:
    group_size: 64 # Contiguous channel group size to take median
    ignore_channels: [] # Channels (zero-indexed) to drop from median calculation 

- preprocess.set_zero:
    channels: [] # Channels (zero-indexed) to set to zero prior to snippeting stage (should likely be the same as ignore_channels above)

- snippet.fast_threshold:
    snippet_length: 64 # Snippet length
    detect_threshold: 50 # Detection threshold (microvolts)
    return_threshold: 20 # Return threshold (microvolts)
    return_samples: 8 # Minimum return time (# samples)
    n_channels: 4 # Number of channels per channel group

- checkpoint:
    file: /n/holylfs02/LABS/olveczky_lab/Anand/data/snippets.h5 # Snippets are stored as a single HDF5 file
    batch_size: 1000 # Batch size determines chunking for next stage; set this to inf to cluster over the whole dataset (warning: N^2 operation)
    batch_overlap: 0 

- label:
    transform:
        - beta_multiply:
            beta: 1
        - wavelet_denoise:
            wavelet: sym2 # Wavelet used in discrete wavelet transform prior to PCA. For options, see http://wavelets.pybytes.com/
    cluster:
        isosplit:
            n_components: 10 # No. PCA components to use for clustering
            isocut_threshold: 0.9
            min_cluster_size: 8 # Minimum cluster size to consider splitting
            K_init: 200 # Over-clustering initialization
            refine_clusters: False 
            max_iterations_per_pass: 500
            jitter: 0.001 # Additive elementwise Gaussian noise to separate duplicate vectors
    link:
        isosplit: # Link using the ISO-SPLIT cluster split test
            n_components: 10 # No. PCA components to use for clustering
            isocut_threshold: 0.9
            min_cluster_size: 8 # Minimum cluster size to consider splitting
            K_init: 200 # Over-clustering initialization
            refine_clusters: False 
            max_iterations_per_pass: 500
            jitter: 0.001 # Additive elementwise Gaussian noise to separate duplicate vectors
            max_cluster_uses: 2 # Maximum number of times a cluster can be used in a link (normally 1, but increase to correct for cluster split errors)
    n_channels: 4 # Number of channels represented in each snippet (in this case, tetrode)
    link_in_feature_space: true

- checkpoint:
    file: /n/holylfs02/LABS/olveczky_lab/Anand/data/linked_snippets.h5 # Clustered snippets are stored as a single HDF5 file
    batch_size: 100000 # Batch size determines chunking for next stage
    batch_overlap: 0

- postprocess.label_noise_clusters # Auto-label clusters as noisy for GUI using class-averages computed in batches of 100000
```

Once you've edited the results using the GUI, you can finalize the labels and extract the spike times using [finalize.yaml](finalize.yaml). This will create a new `.h5` file, containing the final labels and spike times.

You can add, delete, or reorder any available processing stages, and `ephys2` will ensure the input and output types match before running any computation (see [Handling failures](../slurm/README.md#handling-failures)). The easiest way to get started is to copy and modify one of the example configuration files above. If you'd like to contribute one, open a [merge request](https://gitlab.com/OlveczkyLab/ephys2/-/merge_requests).

## Available processing stages

Documentation for the available stages in `Ephys2` is coming soon; for now, refer to the above examples.
