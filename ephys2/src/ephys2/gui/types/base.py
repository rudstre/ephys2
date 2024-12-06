'''
Base types for GUI
'''
from typing import Union, Callable, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from contextlib import contextmanager

'''
Basic widget store implementing the Redux FRP pattern.
https://redux.js.org/
'''

''' Store state as nested dictionary with string keys '''

GUIState = Union[Dict[str, Any], Dict[str, 'GUIState']]

''' Store actions which can update the state '''

@dataclass
class GUIAction:
	tag: str
	payload: Any = None

''' Store ''' 

class GUIStore(ABC):
	'''
	A singleton data structure containing "subscribable" fields, where the 
	singleton is addressed by the class name.
	'''

	def __init__(self):
		self.state: GUIState = self.initial_state()
		self.subscribers: Dict[str, List[Callable]] = dict()
		self._atomic = False
		self._queued_cbs = []

	@abstractmethod
	def initial_state(self) -> GUIState:
		'''
		Declare the initiate state of the store.
		This should set all structure (i.e. keys), whereas values will change with time.
		'''
		pass

	@abstractmethod
	def dispatch(self, action: GUIAction):
		'''
		Dispatch changes which update the state.
		Uses the internal __setitem__ API to notify any subsribers.
		'''
		pass

	def subscribe(self, path: str, callback: Callable):
		'''
		Subscribe to changes on a particular data path.
		'''
		if not (path in self):
			raise ValueError(f'Path {path} not found in the store')
		elif path in self.subscribers:
			self.subscribers[path].append(callback)
		else:
			self.subscribers[path] = [callback]

	def unsubscribe(self, path: str, callback: Callable):
		'''
		Unsubscribe from changes on a particular data path.
		'''
		if path in self.subscribers:
			self.subscribers[path].remove(callback)
		else:
			raise ValueError(f'Path {path} not found in the subscriber set')
			
	def __getitem__(self, key: str):
		'''
		Keys are given in filepath-like format, a/path/to/some/value
		'''
		val = self.state
		for subkey in key.split('/'):
			val = val[subkey]
		return val

	def __contains__(self, key: str):
		'''
		Check if the store contains a path.
		'''
		try:
			val = self[key]
		except:
			return False
		return True

	@contextmanager
	def atomic(self):
		'''
		Gives a way to perform multiple writes atomically before any notifications are sent.
		'''
		nested_atomic = self._atomic # Whether an outer atomic block is active
		self._atomic = True
		yield
		if not nested_atomic:
			for callback in self._queued_cbs:
				callback()
			self._queued_cbs = []
			self._atomic = False

	''' Private API '''

	def __setitem__(self, key: str, val: Any):
		'''
		Modify state, and notify any subscribers.
		Using setter directly can put application in an inconsistent state.
		TODO: should use threading / asynchronicity
		'''
		_state = self.state
		_subkey = key
		for subkey in key.split('/')[:-1]:
			_state = _state[subkey]
			_subkey = subkey
		_state[_subkey] = val

		if key in self.subscribers:
			for callback in self.subscribers[key]:
				if self._atomic:
					self._queued_cbs.append(callback)
				else:
					callback()


@dataclass
class StoreLink:
	'''
	Mechanism for linking fields of two stores while avoiding mutual recursion.
	'''
	field: str
	store1: GUIStore
	store2: GUIStore
	propagate: Callable[[GUIStore, GUIStore], None]
	dirty_bit: bool = False

	def __post_init__(self):
		# Link the stores
		self.store1.subscribe(self.field, lambda: self.run(self.store1, self.store2))
		self.store2.subscribe(self.field, lambda: self.run(self.store2, self.store1))

	def run(self, storeA, storeB):
		if not self.dirty_bit:
			self.dirty_bit = True # Acquire
			self.propagate(storeA, storeB)
			self.dirty_bit = False # Release

class GUIWidget:
	'''
	Base class for all GUI widgets.
	Tracks subscriptions to the store and removes them upon deletion.
	Intended to be used only in multiple inheritance with some QtWidget class.
	'''
	def __init__(self, store: GUIStore):
		self.store = store
		self._subscriptions = []

	def subscribe_store(self, path: str, callback: Callable):
		'''
		Subscribe to changes on a particular data path.
		'''
		self._subscriptions.append((path, callback))
		self.store.subscribe(path, callback)

	def deleteLater(self):
		'''
		Remove subscriptions to the store.
		'''
		for path, callback in self._subscriptions:
			self.store.unsubscribe(path, callback)
		super().deleteLater()