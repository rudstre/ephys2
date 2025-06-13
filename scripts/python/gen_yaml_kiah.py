'''
Generate FAST-ISOSPLIT configuration files for a directory with the following structure:

outer_directory/
	session/
		ephys_folder/
			*.rhd

To use this file, run in your terminal:
pip install pyyaml

Then change the parameters below as necessary.
'''

outer_directory = '/Users/anandsrinivasan/dev/fasrc/data/test_folder' # Set this to your outer directory (give absolute path)

ephys_folder = 'ephys' # Set this to the name of your inner ephys directory 

config_str = '''
- input.rhd2000:
    files: SET_ME # (this will be set automatically)
    start: 0
    stop: inf # Set to inf to read whole file
    batch_size: 450000 # Processing batch size 
    batch_overlap: 0 

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
    file: SET_ME # (this will be set automatically)
    batch_size: 20000 # Ensure this is a multiple of the following overlap 
    batch_overlap: 10000 # Since of overlapping instances of clustering

- label_old.isosplit_segfuse:
    block_size: 10000 # Perform separate instances of clustering within blocks (increase to detect lower-firing-rate units better)
    n_components: 10 # No. PCA components to use for clustering
    isocut_threshold: 0.8 # Partition threshold; decrease to produce more clusters
    min_cluster_size: 8 # Minimum cluster size to consider splitting
    K_init: 200 # Over-clustering initialization (should be larger than max expected # units)
    refine_clusters: False
    max_iterations_per_pass: 700
    jitter: 0.001 # Additive elementwise Gaussian noise to separate duplicate vectors
    link_threshold: 0.0 # Threshold for linking two nodes across cluster trees (lower means more links)
    link_sig_s: 0.005 # Sigmoidal scale parameter for link weights
    link_sig_k: 0.03 # Sigmoidal offset parameter for link weights (higher means more links)

- checkpoint:
    file: SET_ME # (this will be set automatically)
    batch_size: 10000 # Batch size determines chunking for next stage; since this is the last step, this has no effect.
    batch_overlap: 5000
'''

if __name__ == '__main__':
	import yaml
	import os
	import glob
	import pdb


	assert os.path.isdir(outer_directory), f'{outer_directory} should be a directory'
	for session_folder in sorted(os.listdir(outer_directory)):

		# Construct per-session paths
		ephys_path = os.path.join(outer_directory, session_folder, ephys_folder)
		rhd_path = os.path.join(ephys_path, '*.rhd')
		snippets_path = os.path.join(ephys_path, 'snippets.h5')
		linked_snippets_path = os.path.join(ephys_path, 'linked_snippets.h5')
		config_path = os.path.join(ephys_path, 'config.yaml')

		# Construct per-session configuration
		session_config = yaml.safe_load(config_str)
		session_config[0]['input.rhd2000']['files'] = rhd_path
		session_config[5]['checkpoint']['file'] = snippets_path
		session_config[7]['checkpoint']['file'] = linked_snippets_path

		# Write per-session configuration
		with open(config_path, 'w') as file:
			yaml.dump(session_config, file, default_flow_style=False)

		print(f'Wrote configuration in {config_path}')
