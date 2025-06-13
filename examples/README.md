# Guide to YAML Config Files

## Parameter Descriptions and Resource Guidelines for clustering/linking

Below are explanations of key parameters in the clustering/linking stage, along with recommendations for choosing batch sizes, number of CPU cores, and maximum memory allocation.

### Batch Size

- **`batch_size`**  
  Defines the number of spikes (or samples) processed in each block. A larger batch size (e.g., **700,000**) yields more data per block, which can improve clustering consistency but increases both memory and computation time. If a neuron does not fire for longer than the batch size (in spikes), it cannot be linked across batches by ISO‑SPLIT.  
  - **Suggested value**: `500000`  

### Number of CPU Cores
- **`cores`**  
  Number of CPU threads allocated to the job. `ephys2` parallelizes over batch processing (splitting, clustering, linking) and benefits from multiple cores.  
  - Keep it under **4 cores per week of recording for a batch size of 500,000** or else it might freeze due to MPI issues. This needs to scale inversely with batch size.
    - In practice, this will usually be more limited by memory requirements than MPI issues (see below).

### Memory Estimation

- A good rule of thumb is:

  ```
  Memory (GB) ≈ 22 × N × (batch_size / 100000)
  ```

  where:  
  - `N` = number of CPU cores  
  - `batch_size / 100000` = batch‐size factor (e.g., 2 if `batch_size = 200000`)  
  - **Example**: If you allocate `7` cores and `batch_size = 500000`, then memory ≈ 22 GB × 7 × 5 = **770 GB**.  

- **Guidelines**:  
  - Always round up and leave ~20–30% headroom (e.g., request ~1.3× the estimated memory).  
  - If you run out of memory, decrease `batch_size` or reduce the number of cores.  
  - Monitor a short test run (e.g., one batch) to measure actual memory usage before scaling to the full dataset.


### Clustering Parameters
- **`beta`** (in both `cluster` and `link` stages)  
  - **What it does**: Controls how “peak‐sensitive” the clustering is. A high `beta` value weights amplitude differences more heavily during clustering, producing tighter clusters in amplitude‐space. Lower `beta` makes clustering less amplitude‐dependent (more reliant on waveform shape).  
  - **Suggested range**: `1–100`  
  - **Notes**:  
    - **`beta = 100`** is a common default for tetrode data.  
    - If your dataset has low SNR or widely varying amplitudes, try lowering to `beta = 10`.
    - Adjusts the required `isocut_threshold` (see below).

- **`K_init`** (in the `cluster` stage)  
  - **What it does**: Sets the initial number of over‑clustered centroids for ISO‑SPLIT. The algorithm starts with `K_init` clusters and then merges them based on `isocut_threshold`.  
  - **Suggested value**: For `batch_size = 500000`, use `1000`.  
  - **Notes**:  
    - Increase `K_init` linearly with `batch_size` (e.g., `batch_size = 100000` → `K_init = 200`).  
    - Too low a `K_init` can force distinct units to merge prematurely; too high a `K_init` increases compute time without benefit.

- **`cluster:isocut_threshold`**  
  - **What it does**: Governs merging within a single batch. A higher value merges less‐similar clusters (more aggressive merging).  
  - **Suggested value**: `1`
  - **Notes**:  
    - If you see too many small clusters (over‐segmentation), increase this by ~0.1–0.2. If distinct units are merging incorrectly, lower it.  
    - Consider decrease the threshold by ~10% for every 10x decrease in `beta` (and vice-versa).

### Linking parameters
#### Segmentation Fusion Linking Parameters (Recommended)

These parameters are used when applying `segmentation_fusion` in the `link` stage. This method is generally recommended over traditional `isocut`-based linking.

##### Change this first:
- **`segmentation_fusion:link_sig_k`**  
  - **What it does**: Sets the *offset* of the sigmoid function used to transform distances into linking weights. Larger values shift the sigmoid to permit more links overall.  
  - **Suggested default**: `0.05`  
  - **Notes**:  
    - Increase this if you want more aggressive linking across batches. Decrease if over-linking is occurring.
    - Normal range is `.02 - .07`

##### Change this second:
- **`segmentation_fusion:link_threshold`**  
  - **What it does**: Controls the base threshold for linking clusters across adjacent batches. Lower values make linking *easier* (more permissive), while higher values make linking stricter.  
  - **Suggested default**: `0.02`  
  
##### Rarely change this:
- **`segmentation_fusion:link_sig_s`**  
  - **What it does**: Sets the *scale* of the sigmoid function applied to linking weights, which controls how sharply the linking weight falls off near the threshold.
  - **Suggested default**: `0.005`  

#### ISO-SPLIT Linking Parameters (Alternative)

Although `segmentation_fusion` is generally preferred, you may optionally use `isocut_threshold` for traditional ISO-SPLIT–style linking across batches.

- **`link:isocut_threshold`**  
  - **What it does**: Determines how permissive linking is in feature space between batches. Higher thresholds allow less‐similar clusters to link (more aggressive linking).  
  - **Suggested value**:  
    ```
    5 × sqrt(B)
    ```  
    where `B` = batch size in units of 100,000 (e.g., if `batch_size = 500000`, then `B = 5` → threshold ≈ 5×√5 ≈ 11.2).
  - **Notes**:  
    - If clusters that should link are not being linked, raise the threshold by ~0.5. If false merges occur, lower it.
    - Consider decreasing the threshold by ~10% for every 10x decrease in `beta`.


### Putting It All Together: Resource Allocation Example

For a week-long recording:

1. **Choose** `batch_size = 500000`  
2. **Compute** cores ≈ 4 cores × (1 week) = **4 cores**  
3. **Estimate** memory = 22 GB × 4 cores × (500000 / 100000) = **440 GB**. Requesting **500 GB** would be a good starting point.  
4. **Set** `batch_overlap = 250000` (50% of batch size).  
5. **Start with**:  
   - `beta = 100`  
   - `cluster:isocut_threshold = 1`  
   - `K_init = 200`  
   - `link_threshold: 0.02`
   - `link_sig_s: 0.005`
   - `link_sig_k: 0.05`
  
Always test a single batch on a small subset of data before scaling to the full dataset and refine these values as needed.

# Example Ephys2 Workflows

To get started, copy one of the files in this directory and start modifying the parameters. Make sure the filepaths point to your data. We recommend using absolute filepaths always (use the `pwd` command in a directory).

## Examples

- [snippet.yaml](snippet.yaml): Snippet a standard RHD2000 file.  
- [snippet_ofps.yaml](snippet_ofps.yaml): Snippet an Intan "one file per signal type" directory.  
- [snippet_multi.yaml](snippet_multi.yaml): Snippet multiple RHD2000 files, explicitly specified.  
- [snippet_multi_pattern.yaml](snippet_multi_pattern.yaml): Snippet multiple RHD2000 files, specified using a wildcard `*` pattern.  
- [label.yaml](label.yaml): Label a previously snippetted (and possibly compressed) dataset (e.g., results of `snippet.yaml` or `snippet_and_compress.yaml`).  
- [snippet_and_label.yaml](snippet_and_label.yaml): Snippet and label an RHD2000 file, without an intermediate compression step (suitable for short-term recordings).  
- [fast.yaml](fast.yaml): Run the entire FAST algorithm on an RHD2000 file.  
- [fast_rhd64.yaml](fast_rhd64.yaml): Run the entire FAST algorithm on an RHD file in the FAST 64-channel RHD format.  
- [fast_mearec.yaml](fast_mearec.yaml): Run the FAST algorithm on a MEArec (Neuron)-generated synthetic spike dataset.  
- [spc_dhawale.yaml](fast_dhawale.yaml): Run the FAST algorithm on the [Zenodo synthetic spike dataset](https://zenodo.org/record/886516#.YiFMg1jML0o).  
- [crcns_hc1.yaml](crcns_hc1.yaml): Download & process a recording from the [CRCNS-HC1 dataset](https://crcns.org/data-sets/hc/hc-1/about).  
- [isosplit_manual.yaml](fast_isosplit_manual.yaml): Run the FAST algorithm using ISO-SPLIT for the clustering step, with a manual curation step.  
- [isosplit_manual_onefile.yaml](fast_isosplit_manual_onefile.yaml): Like the previous, but uses pass-through serialization to write everything to a single file (for large jobs, this will generally be a lot faster, about 1.5–3×).  
- [isosplit_auto.yaml](fast_isosplit_auto.yaml): Run the FAST algorithm using ISO-SPLIT for the clustering step, without a manual curation step.  
- [mr_isosplit_benchmark.yaml](mr_isosplit_benchmark.yaml): Example using ISO-SPLIT with the segmentation fusion step on synthetic spike data.  
- [finalize.yaml](finalize.yaml): Finalize the links into labels after editing the clustering using the GUI (isosplit).  
- [postprocess_label.yaml](postprocess_label.yaml): Use an XGBoost classifier to auto-label noise clusters (for use in GUI).  
- [postprocess_filter.yaml](postprocess_filter.yaml): Same as above, but this one explicitly filters the noise clusters.  
- [label_multi.yaml](label_multi.yaml): Run the labeling step across multiple input snippets files, with automatic re-offsetting of the time index based on start times contained in the files.  
- [resummarize.yaml](resummarize.yaml): Re-compute the summarization for a dataset (necessary, for example, if you split clusters in the detailed view, or if you want to downsample data at a different rate).  
- [relabel.yaml](relabel.yaml): Re-run the labeling step for a dataset in-place (for example to try different clustering parameters).

## Write Your Own

`ephys2` pipelines are specified using [YAML](https://lzone.de/cheat-sheet/YAML) configuration files. Here's an example (taken from the latest pipeline, [isosplit_link.yaml](isosplit_link.yaml)):

> **Important**: When specifying session names with a date pattern match, consult [https://strftime.org](https://strftime.org) for the correct codes.

```yaml
# Link & label using ISO-SPLIT
# ============================

- input.rhd2000:
    sessions: /n/holylfs02/LABS/olveczky_lab/Anand/data/r4_210612_195804.rhd # Path to RHD file  
    datetime_pattern: "*_%y%m%d_%H%M%S" # Pattern to extract timestamps from the filenames (ensure to put in double-quotes; simply pass "*" to ignore patterns) – ensures a consistent sample index across multiple files.  
    batch_size: 450000 # Processing batch size  
    batch_overlap: 0  
    aux_channels: []

- preprocess.bandpass:
    order: 4 # Filter order (increase to obtain better filter response, at the expense of performance and numerical stability)  
    highpass: 300 # Highpass filter frequency (Hz)  
    lowpass: 7500 # Lowpass filter frequency (Hz)  
    Rp: 0.2 # Maximum ripple in the passband (dB)  
    Rs: 100 # Minimum attenuation in the stopband (dB)  
    type: ellip # Filter type (options: `ellip`, `cheby1`, `cheby2`), see [SciPy IIR design docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.iirdesign.html)  
    padding_type: odd # Signal extension method (others supported: `odd`, `even`)  
    padding_length: 1000 # Edge padding length (samples)

- preprocess.median_filter:
    group_size: 64 # Contiguous channel group size to take median  
    ignore_channels: [] # Channels (zero-indexed) to drop from median calculation

- preprocess.set_zero:
    channels: [] # Channels (zero-indexed) to set to zero prior to snippeting stage (should likely match ignore_channels above)

- snippet.fast_threshold:
    snippet_length: 64 # Snippet length (samples)  
    detect_threshold: 50 # Detection threshold (μV)  
    return_threshold: 20 # Return threshold (μV)  
    return_samples: 8 # Minimum return time (samples)  
    n_channels: 4 # Number of channels per channel group

- checkpoint:
    file: /n/holylfs02/LABS/olveczky_lab/Anand/data/snippets.h5 # Snippets stored as a single HDF5 file  
    batch_size: 1000 # Batch size determines chunking for next stage; set to `inf` to cluster over entire dataset (warning: N² operation)  
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
    file: /n/holylfs02/LABS/olveczky_lab/Anand/data/linked_snippets.h5 # Clustered snippets stored as a single HDF5 file  
    batch_size: 100000 # Batch size determines chunking for next stage
    batch_overlap: 0

- postprocess.label_noise_clusters # Auto-label clusters as noisy for GUI using class‑averages computed in batches of 100000
```

Once you've edited the results using the GUI, you can finalize the labels and extract the spike times using [finalize.yaml](finalize.yaml). This will create a new `.h5` file containing the final labels and spike times.

You can add, delete, or reorder any available processing stages, and `ephys2` will ensure the input and output types match before running any computation (see [Handling failures](../slurm/README.md#handling-failures)). The easiest way to get started is to copy and modify one of the example configuration files above. If you'd like to contribute one, open a [merge request](https://gitlab.com/OlveczkyLab/ephys2/-/merge_requests).

## Available Processing Stages

Documentation for the available stages in `Ephys2` is coming soon; for now, refer to the examples above.
