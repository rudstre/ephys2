"""
The universe of stages available in Ephys2
"""

from ephys2.lib.types import *

from .input.stages import STAGES as input_stages
from .preprocess.stages import STAGES as preprocess_stages
from .snippet.stages import STAGES as snippet_stages
from .transform.stages import STAGES as transform_stages
from .label_old.stages import STAGES as label_old_stages
from .extract.stages import STAGES as extract_stages
from .benchmark.stages import STAGES as benchmark_stages
from .postprocess.stages import STAGES as postprocess_stages

# Top-level stages
from .checkpoint import CheckpointStage
from .load import LoadStage
from .label import LabelStage
from .finalize import FinalizeStage

# Test stages
from .test.stages import STAGES as test_stages

ALL_STAGES = {
    "input": input_stages,
    "preprocess": preprocess_stages,
    "snippet": snippet_stages,
    "transform": transform_stages,
    "extract": extract_stages,
    "benchmark": benchmark_stages,
    "test": test_stages,
    "postprocess": postprocess_stages,
    "label_old": label_old_stages,
    CheckpointStage.name(): CheckpointStage,
    LoadStage.name(): LoadStage,
    LabelStage.name(): LabelStage,
    FinalizeStage.name(): FinalizeStage,
}
