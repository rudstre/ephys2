'''
Extraction stages
'''

from .times import TimesStage

STAGES = {
	TimesStage.name(): TimesStage,
}