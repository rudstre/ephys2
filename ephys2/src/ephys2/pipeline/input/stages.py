'''
Input stages
'''

from .rhd2000 import RHD2000Stage
from .rhd64 import RHD64Stage
from .intan_ofps import IntanOfpsStage
from .synthetic.stages import STAGES as SYNTHETIC_STAGES
from .crcns_hc1.stage import CRCNS_HC1Stage
from .dhawale.stages import STAGES as DHAWALE_STAGES


STAGES = {
	RHD2000Stage.name(): RHD2000Stage,
	RHD64Stage.name(): RHD64Stage,
	IntanOfpsStage.name(): IntanOfpsStage,
	CRCNS_HC1Stage.name(): CRCNS_HC1Stage,
	'dhawale': DHAWALE_STAGES,
	'synthetic': SYNTHETIC_STAGES,
}