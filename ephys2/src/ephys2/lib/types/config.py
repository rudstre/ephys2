'''
Configuration & parameter data types
'''

from typing import Dict, List, Callable, Any, Union, NewType, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import glob
import os
from abc import ABC, abstractmethod
import pdb

from ephys2.lib.utils import *
from .base import *

'''
Configuration: possible inputs to a stage
'''

ConfigValue = Union[str, int, float, bool, FilePath, ROFilePath, RWFilePath, Directory, RORangedFilePath, RangedDirectory, List['ConfigValue']]
Config = Dict[str, Union[ConfigValue, 'Config']]

'''
Parameters: possible ways for a stage to request inputs
'''

@dataclass
class Parameter(ABC):
	units: Optional[str]
	description: str

	@abstractmethod
	def __str__(self):
		pass

	@abstractmethod
	def validate(self, val: Any, effectful: bool=True) -> Any:
		'''
		Validate a given value
		'''
		pass

''' Primitive parameter types ''' 

@dataclass
class BoolParameter(Parameter):

	def __str__(self):
		return 'a boolean value'

	def validate(self, val: Any, effectful: bool=True) -> bool:
		assert type(val) is bool, f'{val} is not a bool'
		return val

@dataclass
class StringParameter(Parameter):

	def __str__(self):
		return 'a string'

	def validate(self, val: Any, effectful: bool=True) -> str:
		assert type(val) is str, f'{val} is not a string'
		return val

@dataclass
class IntParameter(Parameter):
	start: int
	stop: int

	def __str__(self):
		return f'an integer in the range [{self.start}, {self.stop}]'

	def validate(self, val: Any, effectful: bool=True) -> Union[int, float]:
		if val in ['inf', float('inf')]:
			val = np.inf
		else:
			assert type(val) in [float, int], f'{val} is not an integer or inf'
			assert val == int(val), f'{val} is not an integer or inf'
			val = int(val)
		assert self.start <= val <= self.stop, f'{val} is not in the range'
		return val

@dataclass
class FloatParameter(Parameter):
	start: float
	stop: float

	def __str__(self):
		return f'a floating point in the range [{self.start, self.stop}]'

	def validate(self, val: Any, effectful: bool=True) -> float:
		if val in ['inf', float('inf')]:
			val = np.inf
		else:
			assert type(val) in [int, float], f'{val} is not a float'
			val = float(val)
		assert self.start <= val <= self.stop, f'{val} is not in the range'
		return val

@dataclass 
class CategoricalParameter(Parameter):
	categories: List[Any]

	def __str__(self):
		return f'one of {self.categories}'

	def validate(self, val: Any, effectful: bool=True) -> Any:
		assert val in self.categories, f'{val} was not in the set'
		return val

@dataclass
class MultiCategoricalParameter(Parameter):
	categories: List[Any]

	def __str__(self):
		return f'one or more of {self.categories} without replacement'

	def validate(self, val: Any, effectful: bool=True) -> List[Any]:
		if type(val) is list:
			assert all(x in self.categories for x in val), f'one or more of {val} was not in the set'
			assert len(set(val)) == len(val), f'{val} contained duplicate entries'
		else:
			assert val in self.categories, f'{val} was not in the set'
			val = [val]
		return val

@dataclass
class FileParameter(Parameter):

	def __str__(self):
		return f'a file'

	def validate(self, val: Any, effectful: bool=True) -> FilePath:
		assert type(val) is str, f'{val} is not a string'
		return abs_path(val) # Get absolute filepath

@dataclass
class ROFileParameter(FileParameter):

	def __str__(self):
		return f'a readable file'

	def validate(self, val: Any, effectful: bool=True) -> ROFilePath:
		val = super().validate(val, effectful)
		if effectful:
			assert is_file_readable(val), f'{val} is not readable'
		return val

@dataclass
class RWFileParameter(FileParameter):

	def __str__(self):
		return f'a writeable file'

	def validate(self, val: Any, effectful: bool=True) -> RWFilePath:
		val = super().validate(val, effectful)
		if effectful:
			assert is_file_writeable(val), f'{val} is not writeable'
		return val

@dataclass
class DirectoryParameter(Parameter):

	def __str__(self):
		return 'a readable directory'

	def validate(self, val: Any, effectful: bool=True) -> Directory:
		assert type(val) is str, f'{val} is not a string'
		val = os.path.normpath(abs_path(val)) # Get absolute folder path & strip any trailing slashes
		if effectful:
			assert is_dir_readable(val), f'{val} is not a readable directory'
		return val

@dataclass 
class RORangedFileParameter(ROFileParameter):

	def __str__(self):
		return f'a readable file with optional start/stop parameters'

	def validate(self, val: Any, effectful: bool=True) -> RORangedFilePath:
		if type(val) is str:
			val = super().validate(val, effectful)
			return RORangedFilePath(val)
		else:
			assert type(val) is dict, f'{val} was not a dictionary'
			assert 'path' in val, f'{val} was not a dictionary containing path'
			start, stop = 0, np.inf
			ip = IntParameter(None, '', 0, np.inf)
			if 'start' in val:
				start = ip.validate(val['start'], effectful)
			if 'stop' in val:
				stop = ip.validate(val['stop'], effectful)
			assert start <= stop, f'start {start} must be less than or equal to stop {stop}'
			path = super().validate(val['path'], effectful)
			return RORangedFilePath(path, start, stop)

@dataclass
class RangedDirectoryParameter(DirectoryParameter):

	def __str__(self):
		return 'a readable directory with optional start/stop parameters'

	def validate(self, val: Any, effectful: bool=True) -> RangedDirectory:
		if type(val) is str:
			val = super().validate(val, effectful)
			return RangedDirectory(val)
		else:
			assert type(val) is dict, f'{val} was not a dictionary'
			assert 'path' in val, f'{val} was not a dictionary containing path'
			start, stop = 0, np.inf
			ip = IntParameter(None, '', 0, np.inf)
			if 'start' in val:
				start = ip.validate(val['start'], effectful)
			if 'stop' in val:
				stop = ip.validate(val['stop'], effectful)
			assert start <= stop, f'start {start} must be less than or equal to stop {stop}'
			path = super().validate(val['path'], effectful)
			return RangedDirectory(path, start, stop)

''' Composite parameter types ''' 

@dataclass 
class ListParameter(Parameter):
	element: Parameter

	def __str__(self):
		return f'a list of ({self.element})'

	def validate(self, val: Any, effectful: bool=True) -> List[Any]:
		if type(val) is list:
			val = [self.element.validate(x, effectful) for x in val]
		elif type(val) is str and (isinstance(self.element, FileParameter) or isinstance(self.element, DirectoryParameter)):
			# Allow glob pattern-match if sub-type is file or directory; sort alphanumerically
			paths = sorted([x for x in glob.glob(val)]) if effectful else [val]
			if effectful:
				assert len(paths) > 0, f'Could not find at least one filepath matching {val}'
			val = [self.element.validate(x, effectful) for x in paths]
		else:
			val = [self.element.validate(val, effectful)]
		return val

@dataclass
class DictParameter(Parameter):
	fields: 'Parameters'

	def __str__(self):
		return f'a nested parameter' + '\n\t'.join([f'{k}: {v}' for k, v in self.fields.items()])

	def validate(self, val: Any, effectful: bool=True) -> Dict[str, Any]:
		assert type(val) is dict, f'{val} is not a dictionary'
		assert set(val.keys()) == set(self.fields.keys()), f'expected fields: {self.fields.keys()}'
		return {
			k: self.fields[k].validate(val[k], effectful)
			for k in self.fields
		}

@dataclass
class MultiParameter(Parameter):
	options: List[Parameter]

	def __str__(self):
		return f'one or more of {self.options} without replacement'

	def validate(self, val: List[Any], effectful: bool=True) -> List[Any]:
		assert type(val) is list, f'{val} is not a list'
		used = set()
		for i in range(len(val)):
			validated = False
			for j in range(len(self.options)):
				try:
					val[i] = self.options[j].validate(val[i], effectful)
					assert not (j in used), f'Option {self.options[j]} was used more than once'
					used.add(j)
					validated = True
				except:
					pass
			assert validated, f'{val[i]} could not be validated'
		return val

''' Set of all parameters ''' 

Parameters = Dict[str, Parameter]

