'''
Linking algorithms available in ephys2
'''

from .segfuse import SegfuseStage
from .isosplit import IsosplitStage

STAGES = {
    SegfuseStage.name(): SegfuseStage,
    IsosplitStage.name(): IsosplitStage,
}