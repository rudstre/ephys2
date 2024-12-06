"""
XGBoost-based binary classifier stage for rejecting noise clusters

To re-train the model:
1. Run scripts/TrainClassifier.ipynb
2. Then update ephys2/src/ephys2/data/pca_xgb_classifier.p 

Note that this requires snippets to be 256 (4x64)-dimensional.
"""
import pickle
import xgboost
import numpy as np

from ephys2.lib.types import *
from ephys2.data import get_path

class FilterNoiseStage(ProcessingStage):
  '''
  This stage directly filters noisy clusters from data.
  '''
  @staticmethod
  def name() -> str:
    return "filter_noise_clusters"

  def type_map(self) -> Dict[type, type]:
    return {LVMultiBatch: LVMultiBatch}

  def initialize(self):
    self.load_model()

  def load_model(self):
    with open(get_path("pca_xgb_classifier.p"), "rb") as file:
      in_dict = pickle.load(file)
      self.model = in_dict["model"]
      self.pca = in_dict["pca"]

  def predict(self, class_avg: npt.NDArray[np.float32]) -> bool:
    # Suppress outlying values to 0
    class_avg = np.nan_to_num(class_avg, nan=0, posinf=0, neginf=0)
    return self.model.predict(self.pca.transform(class_avg.reshape(1, -1)))

  def process(self, data: LVMultiBatch) -> LVMultiBatch:
    for item_id, item in data.items.items():
      label_mask = np.full(item.size, True)
      labels = np.unique(item.labels)
      for label in labels:
        index = item.labels == label
        class_avg = item.data[index].mean(axis=0)
        if not self.predict(class_avg):
          label_mask[index] = False
      item.labels = item.labels[label_mask]
      item.time = item.time[label_mask]
      item.data = item.data[label_mask]
    return data