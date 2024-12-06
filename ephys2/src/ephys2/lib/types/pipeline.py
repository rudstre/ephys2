'''
Stage & pipeline data types
'''

from ast import Assert
from typing import Dict, List, Callable, Any, Union, NewType, Optional, Tuple
from abc import ABC, abstractmethod
import pandas as pd

from ephys2.lib.mpi import MPI
from ephys2.lib.singletons import logger
from .batch import *
from .config import *

class Stage(ABC):

	@staticmethod
	@abstractmethod
	def name() -> str:
		pass
	
	@staticmethod
	def parameters() -> Parameters:
		return dict()

	def __init__(self, cfg: Config):
		'''
		Do not override or subclass this method; defer all state creation 
		& init-time side effects to self.initialize()

		All stages are initialized with MPI information in instance variables.
		'''
		self.cfg = cfg
		self.comm = MPI.COMM_WORLD
		self.rank = self.comm.Get_rank()
		self.n_workers = self.comm.Get_size()
		self._typechecked = False

	def initialize(self):
		'''
		Defer any side-effects from the constructor to this method.
		Barrier() will be called afterward.
		'''
		pass

	def finalize(self):
		'''
		Optional phase called when all computation is complete.
		Call Barrier() in this function if you wish to synchronize.
		'''
		pass

	@classmethod
	def describe_params(cls: type) -> pd.DataFrame:
		return pd.DataFrame(
			columns = ['Name', 'Type', 'Units', 'Description'],
			data = [
				[param_name, str(param), str(param.units), param.description]
				for param_name, param in cls.parameters().items()
			]
		)

	@classmethod
	def description(cls: type) -> str:
		'''
		Description of stage written in rST
		'''
		return '(none)'

	@abstractmethod
	def typecheck(self, input_type: Optional[type]=None) -> Optional[type]:
		'''
		Typecheck the stage against inputs, and provide an output type
		'''
		pass

class ProducerStage(Stage):

	@abstractmethod
	def produce(self) -> Optional[Batch]:
		pass

class InputStage(ProducerStage):

	@abstractmethod
	def output_type(self) -> type:
		'''
		Type of output of this stage
		'''
		pass

	def typecheck(self, input_type: Optional[type] = None) -> Optional[type]:
		assert input_type is None, f'Input type should be None, got {input_type} instead'
		self._typechecked = True
		self._input_type = input_type
		self._output_type = self.output_type()
		return self._output_type

class ProcessingStage(Stage):

	@abstractmethod
	def type_map(self) -> Dict[type, type]:
		pass

	@abstractmethod
	def process(self, data: Batch) -> Batch:
		pass

	def typecheck(self, input_type: Optional[type] = None) -> Optional[type]:
		logger.debug(f'Stage {self.name()} typechecking with input type {input_type}')
		self._input_type = input_type
		tm = self.type_map()
		if Any in tm:
			assert len(tm) == 1, f'Any type was specified in type_map, but there are other types'
			self._output_type = list(tm.values())[0]
			return self._output_type
		else:
			if input_type in tm: # Exact match takes precedence
				self._output_type = tm[input_type]
				return self._output_type
			for itype in tm: # Subclass match is tried next
				if issubclass(input_type, itype):
					self._output_type = tm[itype]
					return self._output_type
			assert False, f'Input type {input_type} could not be matched to one of the possible types {list(tm.keys())}'

	def output_type(self) -> type:
		return self._output_type

class ReductionStage(ProcessingStage):
	'''
	Stage for reducing results from parallel input or processing stages.
	Like a processing stage, but involves a reduction step.
	In the process() step, this stage should cache any information needed for the reduce() step
	in instance variables.
	'''

	@abstractmethod
	def reduce(self):
		'''
		Reduce results across data from all workers.
		No explicit call to Barrier() is made prior to this function;
		subclasses should make explicitly synchronizing calls like Barrier() 
		or Gather() as needed.
		'''
		pass

	def finalize(self):
		''' Calls self.reduce() with a synchronization ''' 
		self.comm.Barrier()
		self.reduce()

@dataclass
class Pipeline:
	stages: List[Stage]

	def initialize(self):
		for stage in self.stages:
			stage.initialize()

	def __repr__(self) -> str:
		return str([stage.name() for stage in self.stages])

	def describe_params(self) -> List[Tuple[str, pd.DataFrame]]:
		return [
			(
				stage.name(),
				stage.describe_params()
			) for stage in self.stages
		]

	def typecheck(self, input_type: Optional[type] = None) -> Optional[type]:
		self._input_type = input_type
		ty = input_type
		for stage in self.stages:
			try:
				ty = stage.typecheck(ty)
			except AssertionError as e:
				raise TypeError(f'in stage: \n\t{stage.name()} \n{e}')
		self._output_type = ty
		return self._output_type

	@staticmethod
	def parse(stage_defs: List[Config], available_stages: dict, effectful: bool=True, input_type: Optional[type]=None) -> 'Pipeline':
		'''
		Parse a configuration into a validated, typechecked pipeline.
		'''
		stages = []

		for index, stage_def in enumerate(stage_defs):
			if type(stage_def) == str:
				# Stages without any parameters
				stage_def = {stage_def: dict()}
			elif type(stage_def) == dict and len(stage_def.keys()) == 1:
				if list(stage_def.values())[0] is None: # Another way of specifying no parameters
					stage_def = {k: dict() for k in stage_def}
			else:
				raise ValueError(f'Stage {index} is not formatted correctly. Did you forget to indent? Every stage should be formatted as: \n - STAGE_NAME:\n\t param_1: value_1\n\t param_2: value_2\n\t...\n')

			stage_name = list(stage_def.keys())[0]

			if not type(stage_name) == str:
				raise ValueError(f'Expected stage {stage_name} to be a string.')

			stage_path = stage_name.split('.')
			stage_module = available_stages

			for submodule in stage_path:
				if type(stage_module) != dict or not (submodule in stage_module):
					raise ValueError(f'Could not find module {submodule} in stage definition {stage_name}')
				stage_module = stage_module[submodule]

			MyStage = stage_module
			stage_cfg = stage_def[stage_name]
			stage = validate_config_stage(stage_cfg, MyStage, effectful)	
			stages.append(stage)

		pipeline = Pipeline(stages=stages)
		pipeline.typecheck(input_type)
		return pipeline

'''
Validation functions
'''

class ParameterError(Exception):

	def __init__(self, stage_name: str, param_name: str, param: Parameter, error_msg: str):
		super().__init__()
		self.err_msg = f'\nStage {stage_name} expected parameter: \n\t"{param_name}" \nof type: \n\t{str(param)} \nbut {error_msg}'

	def __str__(self) -> str:
		return self.err_msg

def validate_config_stage(cfg: Config, MyStage: type, effectful: bool=True) -> Stage:
	'''
	Validate configuration parameters as far as possible.
	'''
	cfg_keys = set(cfg.keys())

	for key, param in MyStage.parameters().items():

		def validate(condition: bool, error_msg: str):
			if not condition:
				raise ParameterError(MyStage.name(), key, param, error_msg)

		validate(key in cfg, f'could not find it')
		try:
			cfg[key] = param.validate(cfg[key], effectful)
		except AssertionError as e:
			validate(False, str(e))

		# If the parameter validates, remove it from the remainder
		cfg_keys.remove(key)

	# Warn about any unused parameters
	if len(cfg_keys) > 0:
		raise ValueError(f'The following parameters were specified for stage:\n\t{MyStage.name()}\nbut were not used:\n\t{list(cfg_keys)}')

	return MyStage(cfg)

'''
Stage & Pipeline-derived parameter types
'''

@dataclass
class PipelineParameter(Parameter):
	'''
	Specify a pipeline as a parameter
	'''
	available_stages: dict
	input_type: type
	output_type: type

	def __str__(self):
		return f'a pipeline consisting of stages from {list(self.available_stages.keys())}'

	def validate(self, val: List[Config], effectful: bool=True) -> Pipeline:
		assert type(val) is list, f'{val} is not a list'
		pipeline = Pipeline.parse(val, self.available_stages, effectful, self.input_type)
		output_type = pipeline.typecheck(self.input_type)
		assert output_type == self.output_type, f'Pipeline output type {output_type} does not match expected type {self.output_type}'
		return pipeline

@dataclass 
class StageParameter(PipelineParameter):
	'''
	Specify a single stage as a parameter
	'''
	def __str__(self):
		return f'a stage from the set {list(self.available_stages.keys())}'

	def validate(self, val: Config, effectful: bool=True) -> Stage:
		assert type(val) is dict, f'{val} is not a dict'
		pipeline = super().validate([val], effectful)
		assert len(pipeline.stages) == 1, f'Expected a single stage, but got {len(pipeline.stages)}'
		return pipeline.stages[0]