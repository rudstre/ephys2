'''
Conversion of Kilosort output to Ephys2 data formats by Diego
'''
# Sampling rate
fs = 30000

def load_spike_data(kilosort_path, n_samples: int = None):
    time = np.load(os.path.join(kilosort_path, "spike_times.npy"))
    labels = np.load(os.path.join(kilosort_path, "spike_clusters.npy"))
    channels = np.load(os.path.join(kilosort_path, "spikes.waveformsChannels.npy"))
    if n_samples is not None:
        ids = time.flatten() < n_samples
        time = time[ids]
        labels = labels[ids]
        channels = channels[ids, ...]
    return time, labels, channels

def load_csv(path):
    # Load the labels
    with open(path) as file:
        cluster_info = csv.reader(file, delimiter="\t")
        cluster_info = [line for line in cluster_info]
        fields = cluster_info[0].copy()
        del cluster_info[0]
    return cluster_info, fields

def load_clusters(path):
    cluster_info, fields = load_csv(path)
    if "cluster_group" in path:
        index = fields.index("cluster_id")
        cluster_type = fields.index("KSLabel")
    elif "cluster_info" in path:
        index = fields.index("cluster_id")
        cluster_type = fields.index("group")
    else:
        raise ValueError("Cluster file needs to be cluster_group.tsv or cluster_info.tsv")\

    clusters = []
    for clu in cluster_info:
        if any([grp in clu[cluster_type] for grp in ["good", "mua"]]):
            clusters.append(int(clu[index]))
    return clusters

def convert_gt_kilosort_dataset(kilosort_path: str, save_path: str, n_tetrodes: int = 32, n_samples: int = None):
    time, labels, channels = load_spike_data(kilosort_path, n_samples=n_samples)
    
    # If manual labeling, use cluster_info otherwise use cluster_group
    info_path = os.path.join(kilosort_path, "cluster_info.tsv")
    if not os.path.exists(info_path):
        info_path = os.path.join(kilosort_path, "cluster_group.tsv")
    clusters = load_clusters(info_path)

    # If there was subselection via manual labeling, only include the correct clusters. 
    good_spikes = np.isin(labels, np.array(clusters)).flatten()
    time = time[good_spikes]
    labels = labels[good_spikes]
    channels = channels[good_spikes, :]

    # Write the h5 file
    with h5py.File(save_path, "w") as file:
        file.attrs.create("tag", "LTMultiBatch")
        for n_tet in range(n_tetrodes):
            grp = file.create_group(str(n_tet))
            channel_ids = np.arange(n_tet*4, (n_tet+1)*4)
            tetrode_spikes = np.isin(channels[:, 0].flatten(), channel_ids)
            tetrode_time = time[tetrode_spikes]
            tetrode_labels = labels[tetrode_spikes]
            unique_tetrode_labels = np.unique(tetrode_labels)
            for i, ids in enumerate(unique_tetrode_labels): 
                tetrode_labels[tetrode_labels == ids] = i
            grp.create_dataset("time", data=tetrode_time.flatten().astype(np.int64))
            grp.create_dataset("labels", data=tetrode_labels.flatten().astype(np.int64))
        
def convert_kilosort_dataset(kilosort_path: str, save_path: str, n_tetrodes: int = 32, n_samples: int = None):
    time, labels, channels = load_spike_data(kilosort_path, n_samples=n_samples)
    waveforms = np.load(os.path.join(kilosort_path, "spikes.waveforms.npy"))
    waveforms = waveforms[:time.shape[0], ...]
                                     
    # If manual labeling, use cluster_info otherwise use cluster_group
    info_path = os.path.join(kilosort_path, "cluster_info.tsv")
    if not os.path.exists(info_path):
        info_path = os.path.join(kilosort_path, "cluster_group.tsv")
    clusters = load_clusters(info_path)

    # If there was subselection via manual labeling, only include the correct clusters. 
    good_spikes = np.isin(labels, np.array(clusters)).flatten()
    time = time[good_spikes]
    labels = labels[good_spikes]
    channels = channels[good_spikes, :]
    waveforms = waveforms[good_spikes, ...]
    
    # Write the h5 file
    with h5py.File(save_path, "w") as file:
        file.attrs.create("tag", "LVMultiBatch")
        for n_tet in range(n_tetrodes):
            grp = file.create_group(str(n_tet))
            channel_ids = np.arange(n_tet*4, (n_tet+1)*4)
            tetrode_spikes = np.isin(channels[:, 0].flatten(), channel_ids)

            tetrode_time = time[tetrode_spikes]
            tetrode_labels = labels[tetrode_spikes]

            # You need to resort the waveforms beacause kilosort orders them strangely
            tetrode_waveforms = waveforms[tetrode_spikes, :, :4]
            channel_sort = np.argsort(channels[tetrode_spikes, :4], axis=1)
            for i in range(tetrode_waveforms.shape[0]):
                tetrode_waveforms[i, ...] = tetrode_waveforms[i, :, :][:, channel_sort[i, :]]
            if tetrode_waveforms.shape[0] > 0:
                tetrode_waveforms = tetrode_waveforms.reshape((tetrode_waveforms.shape[0], -1)).astype(np.float32)
            else:
                tetrode_waveforms = np.array([], dtype=np.float32)
            unique_tetrode_labels = np.unique(tetrode_labels)
            for i, ids in enumerate(unique_tetrode_labels): 
                tetrode_labels[tetrode_labels == ids] = i
            grp.create_dataset("time", data=tetrode_time.flatten().astype(np.int64))
            grp.create_dataset("labels", data=tetrode_labels.flatten().astype(np.int64))
            grp.create_dataset("data", data=tetrode_waveforms)
        

kilosort_path = "/n/holylfs02/LABS/olveczky_lab/Everyone/dannce_rig/dannce_ephys/duke/2022_02_17_1/ephys/Tetrodes/Tetrode0/"
save_path = os.path.join(kilosort_path, 'kilosort_unlabeled_dataset.h5')
convert_kilosort_dataset(kilosort_path, save_path, n_samples=.5*60*fs)

kilosort_path = "/n/holylfs02/LABS/olveczky_lab/Everyone/dannce_rig/dannce_ephys/duke/2022_02_17_1/ephys/Tetrodes/labeled/"
save_path = os.path.join(kilosort_path, 'kilosort_labeled_dataset.h5')
convert_gt_kilosort_dataset(kilosort_path, save_path, n_samples=.5*60*fs)