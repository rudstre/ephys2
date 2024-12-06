'''
MEArec synthetic data generation stages
'''

from .spikes import MearecSpikesStage

STAGES = {
	MearecSpikesStage.name(): MearecSpikesStage,
}
