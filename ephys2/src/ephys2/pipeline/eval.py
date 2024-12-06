'''
Evaluation of pipelines
'''

from typing import List, Union
import time
import numpy as np
import yaml

from ephys2.lib.types import *
from ephys2.lib.singletons import global_timer, logger, profiler
from ephys2.lib.mpi import MPI

from .stages import ALL_STAGES
from .checkpoint import CheckpointStage

def eval_cfg(cfg: List[Config]):
	'''
	Evaluate pipeline from configuration file
	'''
	if not type(cfg) == list:
		raise ValueError(f'Pipeline configuration should consist of an array of steps.')

	pipeline = Pipeline.parse(cfg, ALL_STAGES)
	eval_pipeline(pipeline)

def eval_pipeline(pipeline: Pipeline):
	'''
	Evaluate pipeline in parallel using v3 batch processing model.
	'''
	comm = MPI.COMM_WORLD
	logger.print(f'Evaluating pipeline using {comm.Get_size()} processes.')
	logger.print(pipeline)
	global_timer.start()

	pipeline.initialize() 
	comm.Barrier() # Wait for all processes to finish initialization
	logger.print('Finished initialization.')

	if len(pipeline.stages) > 0: # If there are stages to run

		def producer_helper(producer: ProducerStage, consumers: List[Stage]):
			N = len(consumers)

			# Execute stages until next checkpoint
			logger.print(f'Starting parallel evaluation of the pipeline...')
			global_timer.start_step('evaluation')

			# Check for a checkpoint and initialize if needed
			i = 0
			while i < N and not isinstance(consumers[i], CheckpointStage):
				i += 1
			has_checkpoint = i < N and isinstance(consumers[i], CheckpointStage)

			# Main evaluation loop
			logger.debug(f'Input: {producer.name()}')

			input_data = producer.produce()
			while not (input_data is None):
				data = input_data
				for j in range(i):
					stage = consumers[j]

					global_timer.start_step(stage.name())
					profiler.start_step(stage.name())
					logger.debug(f'Processing step: {stage.name()}')

					# Time processing stage
					data = stage.process(data)

					global_timer.stop_step(stage.name())
					profiler.stop_step(stage.name())

				# Consume data if at checkpoint
				if has_checkpoint:
					consumers[i].process(data)

				logger.debug(f'Input: {producer.name()}')
				global_timer.start_step(producer.name())
				profiler.start_step(producer.name())

				input_data = producer.produce()

				global_timer.stop_step(producer.name())
				profiler.stop_step(producer.name())

			delta = global_timer.stop_step('evaluation')
			logger.print(f'Finished parallel evaluation of the pipeline in ' + '{0:0.1f} seconds'.format(delta))

			# Finalize all stages until the next checkpoint, if any
			logger.print(f'Starting finalize...')
			for stage in [producer] + consumers[:i]:
				logger.debug(f'Starting finalize: {stage.name()}')
				global_timer.start_step(f'finalize-{stage.name()}')
				profiler.start_step(f'finalize-{stage.name()}')

				stage.finalize()

				delta = global_timer.stop_step(f'finalize-{stage.name()}')
				logger.debug(f'Finished finalize in ' + '{0:0.1f} seconds'.format(delta))
				profiler.stop_step(f'finalize-{stage.name()}')
			logger.print(f'Finished finalize.')

			# Execute checkpoint, if any
			if has_checkpoint:
				logger.print(f'Starting checkpoint...')
				global_timer.start_step('serialization')
				profiler.start_step('serialization')

				# Calls barrier
				consumers[i].serialize()

				delta = global_timer.stop_step('serialization')
				logger.print(f'Finished checkpoint in ' + '{0:0.1f} seconds'.format(delta))
				profiler.stop_step('serialization')

				# Load data from checkpoint only if there are more consumers
				if i+1 < N:
					producer_helper(consumers[i], consumers[i+1:])

		assert issubclass(type(pipeline.stages[0]), ProducerStage)
		producer_helper(pipeline.stages[0], pipeline.stages[1:])

	delta = global_timer.stop()
	logger.print(f'Evaluation finished in ' + '{0:0.1f} seconds'.format(delta))
	global_timer.print()
	profiler.print()
		
