'''
Snippeting stages
'''

from .fast_threshold import FastThresholdStage

STAGES = {
	FastThresholdStage.name(): FastThresholdStage,
}