'''
Test common utility functions
'''
import uuid 
import numpy as np
import pytest

from ephys2.lib.utils import *

@pytest.mark.repeat(10)
def test_uuid_np():
	u = uuid.uuid4()
	v = uuid_to_np(u)
	u_ = np_to_uuid(v)
	v_ = uuid_to_np(u_)
	assert u == u_
	assert np.allclose(v, v_)

def test_lca_path():
	p1 = '/path/to/dir1/file1.ext'
	p2 = '/path/to/dir1/file2.ext'
	p3 = '/path/to/dir2/'

	assert lca_path([p1, p2], False) == '/path/to/dir1'
	assert lca_path([p1, p2, p3], False) == '/path/to'
	assert lca_path(['/'], False) == '/'
	with pytest.raises(AssertionError):
		lca_path([], False)
