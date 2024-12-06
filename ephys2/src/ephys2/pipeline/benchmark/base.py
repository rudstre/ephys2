'''
Base benchmarking stage
'''
from typing import Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from ephys2.lib.types import *


@dataclass_json
@dataclass
class Benchmark(ABC):
	method: str
	dataset: str

class BenchmarksStage(ReductionStage, ABC):

	@staticmethod
	def parameters() -> Parameters:
		return {
			'output_file': RWFileParameter(
				units = None,
				description = 'Filepath where benchmark results will be written to in JSON format'
			),
			'method_name': StringParameter(
				units = None,
				description = 'Name of your pipeline which will be displayed in the benchmark server'
			),
			'dataset_name': StringParameter(
				units = None,
				description = 'Name of the dataset which will be displayed in the benchmark server'
			),
		}

	def reduce(self):
		'''
		Run the benchmark; rank 0 must return the result.
		'''
		bd = self.run_benchmark()
		if self.rank == 0:
			with open(self.cfg['output_file'], 'w') as file:
				file.write(bd.to_json())
				
	@abstractmethod
	def run_benchmark(self) -> Benchmark:
		pass