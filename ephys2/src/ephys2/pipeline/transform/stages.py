'''
Feature transform stages
'''

from .clip import ClipStage
from .beta_multiply import BetaMultiplyStage
from .wavelet_denoise import WaveletDenoiseStage

STAGES = {
	ClipStage.name(): ClipStage,
	BetaMultiplyStage.name(): BetaMultiplyStage,
	WaveletDenoiseStage.name(): WaveletDenoiseStage,
}