from abc import ABC, abstractmethod

class A:

	@classmethod
	def tag(cls) -> str:
		return 'A'

	def f(self):
		print(type(self).tag())

class B(A):
	
	@classmethod
	def tag(cls) -> str:
		return 'B'

	def f(self):
		super().f()

B().f()
