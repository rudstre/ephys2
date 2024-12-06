import sys

try:
	from skbuild import setup
except ImportError:
	print(
		"Please update pip, you need pip 10 or greater,\n"
		" or you need to install the PEP 518 requirements in pyproject.toml yourself",
		file=sys.stderr,
	)
	raise

from setuptools import find_packages, Extension
import platform

# # Add no-binary flag for M1 machines
# no_binary_flag = ' --no-binary :all:' if platform.machine == 'arm64' else ''

with open('README.md', 'r', encoding='utf-8') as fh:
	long_description = fh.read()

setup(
	name='ephys2',
	version='1.0.0',
	author='Anand Srinivasan',
	author_email='asrinivasan@fas.harvard.edu',
	description='Ephys2 Spike-Sorter',
	keywords='',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://gitlab.com/OlveczkyLab/Ephys2',
	project_urls={
		'Documentation': 'https://gitlab.com/OlveczkyLab/Ephys2',
		'Bug Reports': 'https://gitlab.com/OlveczkyLab/Ephys2/issues',
		'Source Code': 'https://gitlab.com/OlveczkyLab/Ephys2',
	},
	package_dir={'': 'src'},
	packages=find_packages(where="src"),
	classifiers=[
		# see https://pypi.org/classifiers/
		'Development Status :: 5 - Production/Stable',

		'Intended Audience :: Developers',
		'Topic :: Software Development :: Build Tools',

		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3 :: Only',
		'License :: OSI Approved :: MIT License',
		'Operating System :: OS Independent',
	],
	python_requires='>=3.9',
	install_requires=[
		'numpy>=1.22.0',
		'scipy>=1.8',
		'mpi4py>=3.1.3',
		'cython',
		'matplotlib',
		'h5py>=3.6.0',
		'colorcet',
		'osqp>=0.4.1',
		'cvxopt',
		'cvxpy>=1.1',
		'pyyaml', 
		'scikit-learn',
		'tqdm',
		'requests',
		'qtpy',
		'pandas',
		'datetime-glob',
		'xgboost',
		'pydmd',
		'pywavelets',
		# 'cr-sparse',
		'dataclasses-json',
		'shortuuid',
	],
	extras_require={
		'dev': ['check-manifest'],
		# 'test': ['coverage'],
	},
	cmake_install_dir="src/ephys2",
	# TODO: set -O3 and inline flags
	include_package_data=True,
	package_data={
		'ephys2': ['data/*', 'docs/*']
	},
)