=================
Processing stages
=================

All processing steps in ``ephys`` adhere to the following basic structure (see :doc:`implementing_stage` for details):

.. code-block:: python
	:force:

	class MyStage(ProcessingStage):

		@staticmethod
		def name() -> str:
			...

		@staticmethod
		def parameters() -> Parameters:
			return {
				'param1': StringParameter(
					units = ...,
					description = ...
				),
				...
			}

		@staticmethod
		def type_map() -> Dict[type, type]:
			...

		def initialize(self):
			...

		def process(self, data: Batch) -> Batch:
			...

		def finalize(self):
			...

Each stage declares:

* the ``name`` by which it can be referenced in configuration files
* the required ``parameters`` which will be used to validate configuration files
* the input-output type mapping
* any initialization procedure
* the function for processing each data batch
* any finalization procedure

During execution, each stage's ``process()`` function is composed with the next. The parallelization across input and output data is handled automatically (see :doc:`overview`).

In this manner, each stage can be designed to consume a fixed amount of memory, which is crucial when running in a large-scale fashion.

To see the available input & processing stages in ``ephys2``, see :doc:`built_stages/index`.