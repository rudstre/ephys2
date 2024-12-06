'''
Synthetic data generation stages
'''

from .spikes import DhawaleSpikesStage

STAGES = {
	DhawaleSpikesStage.name(): DhawaleSpikesStage,
}
