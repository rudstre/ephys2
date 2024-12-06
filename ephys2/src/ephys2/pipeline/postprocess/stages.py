from .filter_noise_clusters import FilterNoiseStage
from .label_noise_clusters import LabelNoiseStage
from .summarize import SummarizeStage
from .split_sessions import SplitSessionsStage

STAGES = {
    FilterNoiseStage.name(): FilterNoiseStage,
    LabelNoiseStage.name(): LabelNoiseStage,
    SummarizeStage.name(): SummarizeStage,
    SplitSessionsStage.name(): SplitSessionsStage,
}