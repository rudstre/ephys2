'''
Clustering algorithms available in ephys2
'''

from .spc import SPCStage
from .isosplit import IsosplitStage

STAGES = {
    SPCStage.name(): SPCStage,
    IsosplitStage.name(): IsosplitStage,
}