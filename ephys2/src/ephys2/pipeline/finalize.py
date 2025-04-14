'''
Apply links and reduce a linked labeling to a simple labeling.
'''

from typing import Dict
import h5py

from ephys2.lib.types import *
from ephys2.lib.cluster import *
from ephys2.lib.singletons import global_state
from ephys2.lib.h5.sparse import *

class FinalizeStage(ProcessingStage):

  @staticmethod
  def name() ->  str:
    return 'finalize'

  def type_map(self) -> Dict[type, type]:
    return {LLVMultiBatch: LVMultiBatch}

  def initialize(self):
    self.excluded_units = dict() # Per-channel group excluded units

  def process(self, data: Batch) -> Batch:
    items = dict()

    for item_id, item in data.items.items():

      # Read metadata (links matrix & excluded units)
      if not (item_id in self.excluded_units):
        assert global_state.last_h5 != None, 'finalize requires an HDF5 data source'
        self.excluded_units[item_id] = np.array([], dtype=np.int64)
        with h5py.File(global_state.last_h5, 'r') as file:
          if 'excluded_units' in file[item_id]:
            self.excluded_units[item_id] = file[item_id]['excluded_units'][:]

      # Since unit exclusion produces a dynamically-sized result, we must remove any possible `overlap` parameter, as it will be inconsistent with the actual data.
      # TODO: Declare fixed- vs. dynamic-output stages at the type level, and throw errors (or warnings at the least) when users provide nonzero `overlap` to dynamically sized stages.
      item.remove_overlap()
      
      # Map labels into linked domain
      linked_time = item.time
      linked_data = item.data
      linked_labels = link_labels(item.labels, item.linkage)

      # Apply unit exclusion
      if self.excluded_units[item_id].size > 0:
        mask = np.full(linked_labels.size, True)
        for exc_label in self.excluded_units[item_id]:
          mask[linked_labels == exc_label] = False
        linked_time = linked_time[mask]
        linked_data = linked_data[mask]
        linked_labels = linked_labels[mask]

      items[item_id] = LVBatch(
        time=linked_time, data=linked_data, labels=linked_labels, overlap=0
      )

    return LVMultiBatch(items=items)
