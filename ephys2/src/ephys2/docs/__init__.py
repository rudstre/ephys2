'''
Non-code resources for Ephys2
'''

import pkg_resources

def get_path(name: str):
	'''
	Get the path of a data file in this directory.
	'''
	return pkg_resources.resource_filename(__name__, name)