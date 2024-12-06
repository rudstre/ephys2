# Run this app with `python -m ephys2.benchmark_server FOLDER` and
# visit http://127.0.0.1:8050/ in your web browser.

import os
import glob
import pdb

from .intrinsic import *
from .extrinsic import *

from ephys2.pipeline.benchmark.intrinsic import *
from ephys2.pipeline.benchmark.extrinsic import *

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser(description='Ephys2 command-line interface')
	parser.add_argument('folder', type=str, help='Benchmarks folder')
	args = parser.parse_args()
	varargs = vars(args)

	if not os.path.isdir(varargs['folder']):
		raise ValueError(f'Folder {varargs["folder"]} does not exist')

	paths = glob.glob(f'{varargs["folder"]}/*.json')
	if len(paths) > 0:
		benchmarks = []
		for path in paths:
			with open(path, 'r') as file:
				benchmarks.append(file.read())

		if 'ExtrinsicBenchmark' in benchmarks[0]:
			assert all('ExtrinsicBenchmark' in bm for bm in benchmarks)
			print('Starting extrinsic benchmarks server')
			app = extrinsic_benchmarks_app([ExtrinsicBenchmark.from_json(bm) for bm in benchmarks])

		if 'IntrinsicBenchmark' in benchmarks[0]:
			assert all('IntrinsicBenchmark' in bm for bm in benchmarks)
			print('Starting intrinsic benchmarks server')
			app = intrinsic_benchmarks_app([IntrinsicBenchmark.from_json(bm) for bm in benchmarks])

		else:
			raise ValueError('Received unrecognized JSON files')

		app.run_server(debug=True)

	else:
		print(f'No JSON files found in {varargs["folder"]}, exiting.')