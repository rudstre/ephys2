"""
XGBoost-based binary classifier stage for rejecting noise clusters

To re-train the model:
1. Run scripts/TrainClassifier.ipynb
2. Then update ephys2/src/ephys2/data/pca_xgb_classifier.p 

Note that this requires snippets to be 256 (4x64)-dimensional.
"""
import h5py

from .filter_noise_clusters import *

from ephys2.lib.h5.sparse import *
from ephys2.lib.cluster import *
from ephys2.lib.types import *
from ephys2.lib.singletons import global_state

class LabelNoiseStage(ReductionStage):
  '''
  Unlike FilterNoiseStage, this stage labels, but does not filter, noisy clusters from data.
  '''
  @staticmethod
  def name() -> str:
    return "label_noise_clusters"

  def type_map(self) -> Dict[type, type]:
    return {LLVMultiBatch: LLVMultiBatch}

  def initialize(self):
    FilterNoiseStage.load_model(self)
    self.excluded_units = dict() # Per-tetrode excluded units

  def add_exclusion(self, item_id: str, label: np.int64):
    if not (item_id in self.excluded_units):
      self.excluded_units[item_id] = set()
    self.excluded_units[item_id].add(label)

  def process(self, data: LLVMultiBatch) -> LLVMultiBatch:
    # Record any excluded units
    for item_id, item in data.items.items():

      # Map labels into the linked domain
      linked_labels = link_labels(item.labels, item.linkage)
      for label in np.unique(linked_labels):
        class_avg = item.data[linked_labels == label].mean(axis=0)
        if not FilterNoiseStage.predict(self, class_avg):
          # Record excluded unit to be written later during checkpointing stage
          # print('Got excluded label for tetrode:', item_id, label)
          self.add_exclusion(item_id, label)

    return data

  def reduce(self):
    # Gather all excluded units to be written to the file
    all_excluded_units = self.comm.gather(self.excluded_units, root=0)
    if self.rank == 0:
      # Write all excluded units (we are in rank 0, so the data's been gathered)
      excluded_units = dict()
      for data in all_excluded_units:
        for item_id, labels in data.items():
          if not (item_id in excluded_units):
            excluded_units[item_id] = set()
          excluded_units[item_id] |= labels

      with h5py.File(global_state.last_h5, 'a') as file:
        for item_id, labels in excluded_units.items():
          if len(labels) > 0:
            item_dir = file[item_id]
            if 'excluded_units' in item_dir:
              # Merge if exists
              labels |= set(item_dir['excluded_units'][:])
              del item_dir['excluded_units']
            # Write the excluded labels
            # print('Wrote excluded labels for tetrode: ', item_id, labels)
            item_dir.create_dataset('excluded_units', data=np.array(list(labels), dtype=np.int64))

