'''
Benchmarking stages
'''
from .intrinsic import *
from .extrinsic import *

STAGES = {
	IntrinsicBenchmarksStage.name(): IntrinsicBenchmarksStage,
	ExtrinsicBenchmarksStage.name(): ExtrinsicBenchmarksStage,
}