'''
Tests of parameter validation mechanisms
'''
import pytest
import numpy as np
import os
from pathlib import Path
from stat import S_IREAD

from ephys2.lib.types.config import *
from tests.utils import *

def make_ro_file(fname: str) -> str:
	fpath = rel_path(f'data/{fname}')
	Path(fpath).touch()
	os.chmod(fpath, S_IREAD)
	return fpath

''' Bool ''' 

def test_bool():
	pm = BoolParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate(1)
	with pytest.raises(AssertionError):
		pm.validate('asdf')
	assert pm.validate(True) == True
	assert pm.validate(False) == False

''' String ''' 

def test_string():
	pm = StringParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate(1)
	with pytest.raises(AssertionError):
		pm.validate(True)
	assert pm.validate('asdf') == 'asdf'

''' Int ''' 

def test_int():
	pm = IntParameter(None, '', 0, np.inf)
	with pytest.raises(AssertionError):
		pm.validate('asdf')
	with pytest.raises(AssertionError):
		pm.validate(-1)
	with pytest.raises(AssertionError):
		pm.validate(1.2)
	assert pm.validate(10) == 10
	assert pm.validate(np.inf) == np.inf

''' Float ''' 

def test_float():
	pm = FloatParameter(None, '', 0, np.inf)
	with pytest.raises(AssertionError):
		pm.validate('asdf')
	with pytest.raises(AssertionError):
		pm.validate(-1)
	assert pm.validate(10) == 10
	assert pm.validate(np.pi) == np.pi
	assert pm.validate(np.inf) == np.inf

''' Categorical ''' 

def test_categorical():
	pm = CategoricalParameter(None, '', ['a', 'b', 'c'])
	with pytest.raises(AssertionError):
		pm.validate('asdf')
	with pytest.raises(AssertionError):
		pm.validate(1)
	assert pm.validate('b') == 'b'

''' File & Directory ''' 

def test_file():
	pm = FileParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate(1)
	assert pm.validate('path/to/file') == abs_path('path/to/file')

def test_ro_file():
	pm = ROFileParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate('/path/to/fake.file')
	assert pm.validate(rel_path('data/sampledata.rhd')) == abs_path(rel_path('data/sampledata.rhd'))

# TODO: try to replicate conditions within container. & Test without root.
def xtest_rw_file():
	pm = RWFileParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate('/path/to/fake.file')
	fp = make_ro_file('test.file')
	with pytest.raises(AssertionError):
		pm.validate(fp)	
	remove_if_exists(fp)
	assert pm.validate(rel_path('data/sampledata.rhd')) == abs_path(rel_path('data/sampledata.rhd'))

def test_directory():
	pm = DirectoryParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate('/path/to/fake/dir')
	dp = rel_path('data')		
	assert pm.validate(dp) == abs_path(dp)

def test_ranged_file():
	pm = RORangedFileParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate('/path/to/fake.file')
	fp = rel_path('data/sampledata.rhd')
	assert pm.validate(fp) == RORangedFilePath(abs_path(fp), 0, np.inf)
	assert pm.validate({'path': fp, 'start': 100, 'stop': 10000}) == RORangedFilePath(abs_path(fp), 100, 10000)
	assert pm.validate({'path': fp}) == RORangedFilePath(abs_path(fp))
	assert pm.validate({'path': fp, 'stop': 1000}) == RORangedFilePath(abs_path(fp), stop=1000)

def test_ranged_directory():
	pm = RangedDirectoryParameter(None, '')
	with pytest.raises(AssertionError):
		pm.validate('/path/to/fake/dir')
	dp = rel_path('data')		
	assert pm.validate(dp) == RangedDirectory(abs_path(dp), 0, np.inf)
	assert pm.validate({'path': dp, 'start': 100, 'stop': 10000}) == RangedDirectory(abs_path(dp), 100, 10000)
	assert pm.validate({'path': dp}) == RangedDirectory(abs_path(dp))
	assert pm.validate({'path': dp, 'start': 500}) == RangedDirectory(abs_path(dp), start=500)

''' List parameter ''' 

def test_list_pm():
	pm = ListParameter(None, '', IntParameter(None, '', 0, np.inf))
	with pytest.raises(AssertionError):
		pm.validate(-1)
	with pytest.raises(AssertionError):
		pm.validate([-1, 10, 100])
	with pytest.raises(AssertionError):
		pm.validate(['asdf'])
	assert pm.validate([0, 10, 100]) == [0, 10, 100]
	assert pm.validate([np.inf, 0, 10]) == [np.inf, 0, 10]

''' Nested parameter ''' 

def test_nested_pm():
	pm = DictParameter(None, '', {
		'field1': IntParameter(None, '', 0, np.inf),
		'field2': StringParameter(None, ''),
	})
	with pytest.raises(AssertionError):
		pm.validate(1)
	with pytest.raises(AssertionError):
		pm.validate({'field1': 1})
	with pytest.raises(AssertionError):
		pm.validate({'field1': 1, 'field2': 'asdf', 'field3': 123})
	with pytest.raises(AssertionError):
		pm.validate({'field1': -1, 'field2': 'asdf'})
	assert pm.validate({'field1': np.inf, 'field2': 'string'}) == {'field1': np.inf, 'field2': 'string'}

def test_nested_pm_2():
	pm = DictParameter(None, '', {
		'field1': IntParameter(None, '', 0, np.inf),
		'field2': DictParameter(None, '', {
			'field2a': FloatParameter(None, '', -1, 1),
		})
	})
	with pytest.raises(AssertionError):
		pm.validate({'field1': 1, 'field2': 123})
	with pytest.raises(AssertionError):
		pm.validate({'field1': np.inf, 'field2': {'field2a': -10}})
	assert pm.validate({'field1': np.inf, 'field2': {'field2a': 0}}) == {'field1': np.inf, 'field2': {'field2a': 0}}

''' Multi parameter '''

def test_multi_pm():
	pm = MultiParameter(None, '', [
		IntParameter(None, '', 0, 10),
		StringParameter(None, '')
	])
	assert pm.validate([]) == []
	assert pm.validate([1]) == [1]
	assert pm.validate([1, 'asdf']) == [1, 'asdf']
	assert pm.validate(['asdf']) == ['asdf']
	with pytest.raises(AssertionError):
		pm.validate([1, 10])
	with pytest.raises(AssertionError):
		pm.validate(['asdf', 'asdf'])
	with pytest.raises(AssertionError):
		pm.validate([1, 'asdf', 10])

def test_multi_pm_2():
	pm = MultiParameter(None, '', [
		DictParameter(None, '', {'a': IntParameter(None, '', 0, np.inf)}),
		DictParameter(None, '', {'b': FloatParameter(None, '', 0, np.inf)})
	])
	assert pm.validate([]) == []
	assert pm.validate([{'a': 1}]) == [{'a': 1}]
	assert pm.validate([{'b': np.inf}]) == [{'b': np.inf}]
	assert pm.validate([{'a': 10}, {'b': np.pi}]) == [{'a': 10}, {'b': np.pi}]
	with pytest.raises(AssertionError):
		pm.validate([{'a': -1}])
	with pytest.raises(AssertionError):
		pm.validate([{'c': 10}])
	with pytest.raises(AssertionError):
		pm.validate([{'a': 1}, {'b': 2}, {'a': 3}])