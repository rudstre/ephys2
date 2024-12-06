'''
Old FAST-style segmentation fusion linking stages
'''

from .spc_segfuse import SPCSegFuseStage
from .isosplit_segfuse import IsosplitSegFuseStage

STAGES = {
	SPCSegFuseStage.name(): SPCSegFuseStage,
	IsosplitSegFuseStage.name(): IsosplitSegFuseStage,
}