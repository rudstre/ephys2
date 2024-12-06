"""Simple end-user interface for interacting with finalized LVBatch ephys2 files.

Ephys2 files are HDF5 files that contain a standardized set of data and metadata
for electrophysiology recordings. This module provides a simple interface for
loading and manipulating this data.
"""
import os
import h5py
import numpy as np
from typing import Union, List, Dict, Tuple, Optional, Any
import dataclasses
from dataclasses import dataclass
from scipy.io import loadmat
from scipy.stats import linregress

DIGITAL_IN_THRESHOLD = .5
OPCON_CORRELATION_THRESHOLD = 0.99
ARDUINO_GAP = 10000
DEFAULT_OPCON_SYNC_PIN = "15"
DEFAULT_DANNCE_CAMERA_TRIGGER_PIN = "15"
ACTIVE_THRESHOLD = .1
DEFAULT_DANNCE_RIG_FPS = 50


def load_digital_in(digital_in_file: str, digital_pin: List[str] = [DEFAULT_OPCON_SYNC_PIN]) -> np.ndarray:
    """Load digital in data from a digital_in.h5 file.

    Args:
        digital_in_file (str): Path to digital_in.h5 file.
        digital_pin (List[str], optional): Digital pin to load. Defaults to DEFAULT_OPCON_SYNC_PIN.

    Returns:
        np.ndarray: Digital in data.
    """    
    triggers = {}
    with h5py.File(digital_in_file, "r") as file:
        for pin in digital_pin:
            triggers[pin] = file[pin]["time"][:]
    return triggers

@dataclass
class Loader:
    """Base class for all loaders."""
    path: str
    digital_pins: List[str] = dataclasses.field(default_factory=lambda: [DEFAULT_OPCON_SYNC_PIN])

    def __post_init__(self):
        """Initialize the loader."""
        self.metadata = self._get_metadata()
        self.session_paths = self.metadata["session_paths"]
        self.analog_in_paths, self.digital_in_paths = self._get_analog_digital_paths()

    def _load_digital_in(self, sessions: Union[str, List[str]]) -> np.ndarray:
        """Load the digital in data from all of the digital_in_paths.

        Args:
            sessions (Union[str, List[str], np.ndarray]): List of sessions to load.
        
        Returns:
            np.ndarray: Digital in data.
        """
        sessions = self._format_sessions(sessions)
        digital_in = []
        for path in self.digital_in_paths:
            for session in sessions:
                if session in path:
                    digital_in.append(load_digital_in(path, digital_pin = self.digital_pins))
        return digital_in

    def _get_metadata(self) -> Dict[str, Any]:
        """Get metadata from the file.

        Returns:
            Dict[str, Any]: Metadata dictionary.
        """        
        with h5py.File(self.path, 'r') as f:
            metadata = eval(f.attrs["metadata"])
        return metadata

    def _get_analog_digital_paths(self) -> Tuple[List[str], List[str]]:
        """Get analog, digital, and aux paths.

        Returns:
            Tuple[List[str], List[str], List[str]]: Analog, digital, and aux paths.
        """
        analog_in_paths = self._get_session_file_paths("analog_in.h5")
        digital_in_paths = self._get_session_file_paths("digital_in.h5")
        return analog_in_paths, digital_in_paths

    def _get_session_file_paths(self, tag: str):
        """Get analog in data for a session.

        Returns:
            List[str]: Analog in paths.
        """        
        paths = []
        for session in self.session_paths:
            # Search for an analog_in file in the session folder.
            path = [
                os.path.join(session, file)
                for file in os.listdir(session)
                if file.endswith(tag)
            ]
            if len(path) == 0:
                paths.append([])
            else:
                paths.append(path[0])
        return paths

    def _check_sessions(self, sessions: List) -> None:
        """Check if a session is valid.

        Args:
            sessions (List): List of sessions to check.
        """        
        if not isinstance(sessions, List):
            raise TypeError(f"Sessions must be a List[str], not {type(sessions)}.")
        for session in sessions:
            if session not in self.session_paths:
                raise ValueError(f"Session {session} not found in file.")

    def _format_sessions(self, sessions: Union[str, List[str]]) -> List[str]:
        """Format sessions.

        Args:
            sessions (Union[str, List[str]]): List of sessions to load.

        Returns:
            List[str]: Formatted list of sessions.
        """        
        if isinstance(sessions, str):
            sessions = [sessions]
        elif sessions is None:
            sessions = self.session_paths    
        self._check_sessions(sessions)
        return sessions

    def load(self, sessions: Union[str, List[str]] = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load spike times and labels from a list of sessions.

        Args:
            sessions (Union[str, List[str]], optional): List of sessions to load. Defaults to all sessions.
        
        Returns:
            Tuple[np.ndarray, np.ndarray, Dict]: Spike times, unique labels, and dictionary mapping unique labels to original labels.
        """
        sessions = self._format_sessions(sessions)
        time_ranges = self._time_ranges(sessions)

        n_unique_labels = 0
        spike_times_all = []
        labels_all = []
        original_labels_map = {}
        with h5py.File(self.path, 'r') as f:
            for channel_group in list(f.keys()):
                spike_times = f[channel_group]["time"][:]
                labels = f[channel_group]["labels"][:]
                
                # Get the spike times and labels within the time ranges.
                labels = np.concatenate([labels[(spike_times >= time_range[0]) & (spike_times <= time_range[1])] for time_range in time_ranges])
                spike_times = np.concatenate([spike_times[(spike_times >= time_range[0]) & (spike_times <= time_range[1])] for time_range in time_ranges])
                
                # Rename the labels to be unique.
                unique_labels = np.unique(labels)
                for idx, label in enumerate(unique_labels):
                    labels[labels == label] = idx + n_unique_labels
                    original_labels_map[idx + n_unique_labels] = {"channel_group": channel_group, "label": label}
                n_unique_labels += len(unique_labels)

                # Append the spike times and labels.
                spike_times_all.append(spike_times)
                labels_all.append(labels)
            
            # Concatenate the spike times and labels.
            spike_times_all = np.concatenate(spike_times_all)
            labels_all = np.concatenate(labels_all)
        return spike_times_all, labels_all, original_labels_map

    def _time_ranges(self, sessions: List[str]) -> np.ndarray:
        """Get the time ranges for a list of sessions.

        Args:
            sessions (List[str]): List of sessions.

        Returns:
            np.ndarray: Time ranges.
        """        
        splits = self.metadata["session_splits"]
        time_ranges = np.zeros((len(sessions), 2))
        for idx, session in enumerate(sessions):
            session_idx = self.session_paths.index(session)
            time_ranges[idx, 1] = splits[session_idx]
            if idx > 0:
                time_ranges[idx, 0] = splits[session_idx - 1] + 1
            else:
                time_ranges[idx, 0] = 0
        return time_ranges
    
    def load_spike_count_matrix(self, sessions: Union[str, List[str]], **kwargs) -> Tuple[np.ndarray, np.ndarray]:
        """Load a spike count matrix.

        Args:
            sessions (Union[str, List[str]], optional): List of sessions to load. 

        Returns:
            Tuple[np.ndarray, np.ndarray]: Spike count matrix and list of neurons.
        """
        raise NotImplementedError
    
    def load_waveforms(self, channel_group: Union[int, str], label: int, sessions: Union[str, List[str]] = None, n_samples: int = 1000, random_state: int = 0) -> np.ndarray:
        """Load waveforms from a single neuron.

        Args:
            channel_group (Union[int, str]): Channel group to load.
            label (int): Label to load.
            sessions (Union[str, List[str]], optional): List of sessions to load. Defaults to all sessions.
            n_samples (int, optional): Number of random samples to load. Defaults to 1000.
            random_state (int, optional): Random state. Defaults to 0.

        Returns:
            np.ndarray: nWaveforms for specifice neuron

        Raises:
            ValueError: If the label is not found in the channel group.
        """        
        sessions = self._format_sessions(sessions)
        time_ranges = self._time_ranges(sessions)

        with h5py.File(self.path, 'r') as f:
            spike_times = f[channel_group]["time"][:]
            labels = f[channel_group]["labels"][:]

            # Get the spike times and labels within the time ranges.
            labels = np.concatenate([labels[(spike_times >= time_range[0]) & (spike_times <= time_range[1])] for time_range in time_ranges])

            # Get the waveforms for the specified neuron.
            idx = labels == label
            if np.sum(idx) == 0:
                raise ValueError(f"Label {label} not found in channel group {channel_group}.")
            np.random.seed(random_state)
            idx = np.sort(np.random.choice(np.where(idx)[0], n_samples, replace=False))
            waveforms = f[channel_group]["data"][idx]
        return waveforms

@dataclass
class OpconEphysLoader(Loader):
    sync_pin: str = DEFAULT_OPCON_SYNC_PIN # Digital pin for opcon syncronization heartbeat.

    def load(self, sessions: Union[str, List[str]] = None, opcon_data_path: str = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load spike times and labels from a list of sessions.

        Args:
            sessions (Union[str, List[str]], optional): List of sessions to load. Defaults to all sessions.
            opcon_data_path (str, optional): Path to opcon data. Defaults to None.

        Returns:
            Tuple[np.ndarray, np.ndarray, Dict]: Spike times, unique labels, and dictionary mapping unique labels to original labels.
        """
        sessions = self._format_sessions(sessions)
        spike_times, labels, original_labels_map = super().load(sessions)
        if opcon_data_path is not None:
            if len(sessions) > 1:
                raise ValueError("Aligning spike times to opcon heartbeat signals across more than one session is not supported.")
            digital_in = self._load_digital_in(sessions=sessions)
            opcon_data = self._load_opcon_data(opcon_data_path)
            spike_times, digital_in = self._remap_spike_times(spike_times, digital_in[0], opcon_data)
            return spike_times, labels, original_labels_map, digital_in
        else:
            return spike_times, labels, original_labels_map

    def _load_opcon_data(self, opcon_data_path: str) -> np.ndarray:
        """Load opcon data.

        Args:
            opcon_data_path (str): Path to opcon_data.mat file

        Returns:
            np.ndarray: Opcon sync data.
        """
        opcon_data = loadmat(opcon_data_path)
        return opcon_data["gpio_time"][:]

    def _remap_spike_times(self, spike_times: np.ndarray, digital_in: dict, opcon_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Remap spike times to opcon time base.

        Remap spike times to opcon time base by fitting a linear regression between the digital in and opcon data.

        Args:
            spike_times (np.ndarray): Spike times.
            digital_in (dict): Digital in data.
            opcon_data (np.ndarray): Opcon sync data.

        Returns:
            Tuple[np.ndarray, np.ndarray]: Remapped spike times and digital in data.
        """
        digital_in = digital_in[self.sync_pin]
        digital_in = np.where(digital_in[digital_in > DIGITAL_IN_THRESHOLD])[0]

        if len(digital_in) != len(opcon_data):
            raise ValueError(f"Digital in ({digital_in.shape}) and opcon data ({opcon_data.shape}) are not the same length.")
        
        if np.corrcoef(np.diff(digital_in), np.diff(opcon_data))[0, 1] < OPCON_CORRELATION_THRESHOLD:
            raise Warning(f"Digital in and opcon data are not correlated above {OPCON_CORRELATION_THRESHOLD}.")

        # Fit a linear regression between the digital in and opcon data.
        slope, intercept, _, _, _ = linregress(digital_in, opcon_data)

        # Remap the spike times and digital in data.
        spike_times = (spike_times*slope) + intercept
        digital_in = (digital_in*slope) + intercept
        return spike_times, digital_in

@dataclass
class DannceRigLoader(Loader):
    camera_trigger_pin: str = DEFAULT_DANNCE_CAMERA_TRIGGER_PIN # Digital pin for dannce camera trigger signal.
    arduino_gap: int = ARDUINO_GAP # Minimum pausing gap in arduino signal to indicate the start of the recording.

    def _load_triggers(self, sessions: Union[str, List[str]] = None) -> np.ndarray:
        """Load camera triggers from a list of sessions.

        Args:
            sessions (Union[str, List[str]], optional): List of sessions to load. Defaults to all sessions.

        Returns:
            np.ndarray: Camera trigger data.
        """
        sessions = self._format_sessions(sessions)
        digital_in = self._load_digital_in(sessions=sessions)
        return [di[self.camera_trigger_pin] for di in digital_in]

    def spike_count_matrix(self, sessions: Union[str, List[str]], n_frames: int) -> Tuple[np.ndarray, np.ndarray, dict]:
        """Generate a matrix of spike counts per frame.

        Args:
            sessions (Union[str, List[str]]): List of sessions to load.
            n_frames (int): Number of frames in the recording session.

        Returns:
            Tuple[np.ndarray, np.ndarray, dict]: Spike count matrix, unique labels, and dictionary mapping unique labels to original labels.
        """
        sessions = self._format_sessions(sessions)
        if len(sessions) > 1:
            raise ValueError("Generating a spike count matrix across more than one session is not supported.")
        
        # Get the trigger bins
        triggers = self._load_triggers(sessions=sessions)[0]
        inds = np.argwhere(np.diff(triggers, prepend=triggers[0]) > self.arduino_gap)
        if len(inds) == 0:
            raise ValueError("The arduino initialization gap could not be found in the trigger data.")
        first = inds[0]
        last = first + n_frames
        bins = np.linspace(triggers[first], triggers[last], n_frames + 1).ravel()

        # Get the spike data
        spike_times, labels, original_labels_map = self.load(sessions=sessions)

        # Get the spike counts within each frame
        unique_labels = np.unique(labels)
        n_units = len(unique_labels)
        spike_counts = np.zeros((n_frames, n_units), dtype=np.uint8)
        for n_unit, clu in enumerate(unique_labels):
            nSpikes, _ = np.histogram(spike_times[labels == clu].astype("float"), bins=bins)
            spike_counts[:, n_unit] = nSpikes
        return spike_counts, unique_labels, original_labels_map

    def get_active_neurons(
        self, spike_counts: np.ndarray, n_partitions=10, active_threshold=ACTIVE_THRESHOLD
    ) -> np.ndarray:
        """Get the active neurons from a unit matrix

        Active neurons have firing rates greater than active_threshold across all partitions.

        Args:
            spike_counts (np.ndarray): Spike count matrix.
            n_partitions (int, optional): Number of partitions to split the recording into. Defaults to 10.
            active_threshold (float, optional): Threshold for active neurons. Defaults to ACTIVE_THRESHOLD.

        Returns:
            np.ndarray: n_neuron, boolean array. True if the neuron was active.
        """
        n_frames = spike_counts.shape[0]
        sample_partitions = np.round(n_frames / n_partitions).astype("int")
        inds = np.arange(0, spike_counts.shape[0], sample_partitions)
        active_test = lambda x: np.nanmean(x, axis=0) * DEFAULT_DANNCE_RIG_FPS > active_threshold
        is_active = active_test(spike_counts)
        for i in range(len(inds[:-1])):
            is_active = is_active & active_test(spike_counts[inds[i] : inds[i + 1], :])
        return is_active
    


