'''
Global metadada
'''
import json

from ephys2.lib.singletons.logger import logger

class Metadata(dict):

	def __init__(self):
		super().__init__()

		# Default values
		self['sampling_rate'] = 30000

	def to_string(self) -> str:
		return json.dumps(self)

	def read_from_string(self, s: str):
		'''
		Note that since this is a singleton object, this is an instance method.
		This will merge metadata stored in string-ified JSON format into the 
		global instance.
		'''	
		logger.print(f'Read metadata: {s}')
		js = json.loads(s)
		for k, v in js.items():
			self[k] = v

global_metadata = Metadata()