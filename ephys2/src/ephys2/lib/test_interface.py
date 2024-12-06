import unittest
from interface import Loader, OpconEphysLoader, DannceRigLoader
import numpy as np


TEST_FILE = '/n/holylfs02/LABS/olveczky_lab/Everyone/dannce_rig/dannce_ephys/bud/2021_06_21_1/ephys/linked_snippets_summarized_multi_finalized.h5'
OPCON_DATA_PATH = "./test_data/opcon_data.mat"

class TestLoader(unittest.TestCase):

    def setUp(self):
        self.loader = Loader(TEST_FILE)

    def test_init(self):
        self.assertTrue("2021_06_21_1" in self.loader.session_paths[0])

    def test_get_metadata(self):
        self.assertTrue(isinstance(self.loader._get_metadata(), dict))

    def test_load(self):
        sessions = self.loader.session_paths[0:2]
        _ = self.loader.load(sessions)

    def test_load_single_session(self):
        sessions = self.loader.session_paths[0]
        _ = self.loader.load(sessions)

    def test_load_waveforms(self):
        sessions = self.loader.session_paths[0]
        _, _, original_labels = self.loader.load(sessions)
        unique_label = list(original_labels.keys())[0]
        channel_group = original_labels[unique_label]["channel_group"]
        label = original_labels[unique_label]["label"]
        waveforms = self.loader.load_waveforms(channel_group, label, sessions = sessions, n_samples = 32, random_state=42)
        self.assertTrue(waveforms.shape == (32, 64*4))

class TestOpconEphysLoader(unittest.TestCase):

    def setUp(self):
        self.loader = OpconEphysLoader(TEST_FILE)

    def test_init(self):
        self.assertTrue("2021_06_21_1" in self.loader.session_paths[0])

    def test_load(self):
        sessions = self.loader.session_paths[0:2]
        _ = self.loader.load(sessions)

    def test_load_single_session(self):
        sessions = self.loader.session_paths[0]
        _ = self.loader.load(sessions)

    # def test_load_opcon_timebase(self):
    #     loader = OpconEphysLoader(TEST_FILE)
    #     sessions = loader.session_paths[0]
    #     _ = loader.load(sessions, opcon_data_path = OPCON_DATA_PATH)

class TestDannceRigLoader(unittest.TestCase):
    def setUp(self):
        self.loader = DannceRigLoader(TEST_FILE)

    def test_init(self):
        self.assertTrue("2021_06_21_1" in self.loader.session_paths[0])

    def test_spike_count_matrix(self):
        sessions = self.loader.session_paths[0]
        n_frames = 540000
        spike_count_matrix, unique_labels, _ = self.loader.spike_count_matrix(sessions, n_frames)
        self.assertTrue(spike_count_matrix.dtype == np.uint8)
        self.assertTrue(spike_count_matrix.shape == (n_frames, len(unique_labels)))

    def test_load_triggers(self):
        sessions = self.loader.session_paths[0:2]
        triggers = self.loader._load_triggers(sessions)
        self.assertTrue(len(triggers) == len(sessions))
    
    def test_get_active_neurons(self):
        sessions = self.loader.session_paths[0]
        n_frames = 540000
        spike_count_matrix, unique_labels, _ = self.loader.spike_count_matrix(sessions, n_frames)
        active_neurons = self.loader.get_active_neurons(spike_count_matrix)
        self.assertTrue(len(active_neurons) == len(unique_labels))

    
if __name__ == '__main__':
    unittest.main()