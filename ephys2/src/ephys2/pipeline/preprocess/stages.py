'''
Preprocessing stages
'''

from .iirfilter import BandpassStage
from .median import MedianFilterStage
from .zero import SetZeroStage
from .decimate import DecimateStage
# from .notch import NOTCH # TODO

STAGES = {
	BandpassStage.name(): BandpassStage,
	MedianFilterStage.name(): MedianFilterStage,
	SetZeroStage.name(): SetZeroStage,
	DecimateStage.name(): DecimateStage,
}