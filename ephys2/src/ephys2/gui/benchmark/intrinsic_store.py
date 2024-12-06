'''
Store for intrinsic benchmarks viewer
'''
from typing import List

from ephys2.pipeline.benchmark.intrinsic import *
from ephys2.gui.types import *

class IntrinsicBenchmarkStore(GUIStore):

  def __init__(self, benchmarks: List[IntrinsicBenchmark], *args, **kwargs):
    self.benchmarks = benchmarks
    super().__init__(*args, **kwargs)

  def initial_state(self) -> GUIState:
    # Data validation
    assert len(self.benchmarks) > 0
    chgroups = set(self.benchmarks[0].chgroups.keys())
    assert all(set(bm.chgroups.keys()) == chgroups for bm in self.benchmarks)
    chgroups = sorted([int(chg) for chg in chgroups])
    return {
      'dataset': self.benchmarks[0].dataset,
      'chgroups': chgroups,
      'current_chgroup': chgroups[0],
      'benchmarks': [bm.chgroups[str(chgroups[0])] for bm in self.benchmarks],
      'methods': [bm.method for bm in self.benchmarks],
    }

  def dispatch(self, action: GUIAction):

    if action.tag == 'up':
      with self.atomic():
        self['current_chgroup'] = min(len(self['chgroups'])-1, self['current_chgroup']+1)
        self['benchmarks'] = [bm.chgroups[str(self['current_chgroup'])] for bm in self.benchmarks]

    elif action.tag == 'down':
      with self.atomic():
        self['current_chgroup'] = max(0, self['current_chgroup']-1)
        self['benchmarks'] = [bm.chgroups[str(self['current_chgroup'])] for bm in self.benchmarks]

    elif action.tag == 'set_chgroup':
      with self.atomic():
        self['current_chgroup'] = action.payload
        self['benchmarks'] = [bm.chgroups[str(self['current_chgroup'])] for bm in self.benchmarks]

    else:
      raise Exception(f'Action of unknown type: {action.tag} received.')