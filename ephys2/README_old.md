This doc is primarily for developers and researchers who will be building this package from source, on their local machine.


# Building from source

Follow these instructions to build `ephys2` on your local machine; all commands are assumed to be run from this directory unless otherwise specified.

## 0. Prep for Windows installation
If you are building on Windows, there are a few extra steps. The easiest (and so far only successful way we've managed to do it) is to use Windows Subsystem for Linux (WSL), a recently developed compatibility layer that allows you to completely simulate a unix environment in Windows without a virtual machine.

### Enable WSL
First, install the WSL command by opening Windows Powershell ***in Administrative Mode*** and typing the following:
```bash
wsl --install
```
You will need to restart your computer after this installation finishes. After the restart, you should be able to open a new application called 'Ubuntu' which gives you direct access to a unix shell.

The central difference between the Windows and Linux install from here on out is that you have to do pretty much everything through the command-line in that Ubuntu shell.

## 1. Anaconda

### Installation

#### Linux and Intel mac
Download and run the [latest conda installer](https://www.anaconda.com/download/).

#### Windows
You will need to install conda through the command line. Click the link above, scroll down to 'Anaconda Installers', right-click on the '64-Bit (x86) Installer' under the Linux tab, and copy the link address. Then run the following in your 'Ubuntu' shell:
```bash
wget <pasted-link>
bash Anaconda3-<version number>-Linux-x86_64.sh
```

#### M1 Mac
If your mac machine has Apple Silicon, you will need to install the `arm64` build of Anaconda. Subsequent C/C++ programs, including MPI, may fail to link otherwise.

You can verify the platform Python is running in using:
```bash
python
>>> import platform
>>> platform.machine()
'arm64' # If this says `x86_64`, you are running under Rosetta and will need to reinstall Conda.
```

Go to [https://github.com/conda-forge/miniforge](https://github.com/conda-forge/miniforge) and download `Mambaforge-MacOSX-arm64`. Run the install script as usual.

### Creating ephys2 environment
#### Linux, Intel Mac, and Windows
Initialize your shell for conda:
```bash
conda init
```
\
Then create a new conda environment:
```bash
conda create -n ephys2 python=3.12
```
\
Then finally activate the environment you just created:
```
conda activate ephys2
```

#### M1 Mac
```bash
mamba create -n ephys2 python=3.12
```

### Installing Python dependencies
You should then install a few packages manually:
```bash
conda/mamba install -c conda-forge numpy scipy matplotlib osqp cvxopt cython
````

**Note for MacOS 13 and above**: ensure you have the latest version of `CMake` installed per [this stackoverflow answer](https://stackoverflow.com/questions/74194672/cmake-problems-after-upgrading-to-macos-13-0).

## If on MacOS
* Ensure you have `clang >= 12.0`. Check by running `clang --version`. If outdated, you may have to either update your XCode command-line tools, or reinstall them by doing:
```bash
sudo rm -rf /Library/Developer/CommandLineTools
sudo xcode-select --install
```

Enabling OpenMP: Apple `clang` ships without OpenMP support by default. If building from source, you may have to install [llvm via homebrew](https://afnan.io/posts/2018-10-01-using-the-latest-llvm-release-on-macos/). Also see [this Stackexchange answer](https://stackoverflow.com/questions/66663120/fatal-error-omp-h-file-not-found-using-clang-on-apple-m1). -->

### GPU acceleration 
NVidia Pascal architecture or better is required (i.e. no K80). See [this issue in cuSignal](https://github.com/rapidsai/cusignal/issues/355#issuecomment-825667739). -->

## 2. MPI (OpenMPI v5.0.0 at time of writing)

### Windows / Linux: build OpenMPI from source 

#### Environment variables & PATH
```bash
export LOCAL_DIR="/usr/local"
echo "export PATH=\"/usr/local/bin:\$PATH\"" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=\"/usr/local/lib:\$LD_LIBRARY_PATH\"" >> ~/.bashrc
source ~/.bashrc
```

#### Download Source Code
 [Download latest tar.gz](https://www.open-mpi.org/software/ompi/) (5.0 at time of writing, use latest stable release.)

##### Windows
Right-click on latest tar.gz and copy address link. Then run the following from the Ubuntu shell:
```bash
wget <pasted-link>
```
You also need to download apt-get Build Essentials in the Ubuntu shell before building:
```bash
sudo apt-get update
sudo apt install build-essential
```

#### Build
<!-- First, you should have ownership and `rwx` permissions on the folder `$LOCAL_DIR`. If you don't, run:
```bash
sudo chown -R $USER $LOCAL_DIR
sudo chmod -R 755 $LOCAL_DIR
``` -->
Then, build OpenMPI from source:
```bash
# * depends on version
tar -xvzf openmpi-*.tar.gz 
cd openmpi-*
# This command may change. Refer to https://docs.open-mpi.org/en/v5.0.x/installing-open-mpi/quickstart.html
./configure --prefix=$LOCAL_DIR --with-libevent=internal --with-hwloc=internal --with-pmix=internal --with-prrte=internal 
# Replace 4 with number of cores
make -j 4 all 
# make install 
sudo make install
```
Check the installed version using `mpirun --version`.

**Important**: If you are re-installing OpenMPI, you may have to manually remove old files from the `$LOCAL_DIR` directory. Sort the files by date using `ls -lth`. 

#### Windows only:
For some reason you must add the MPI path directly to the .bashrc file yourself in order for the system to find the MPI installation.

Run the following in the Ubuntu shell:
```bash
echo "export PATH=\"/usr/local/bin/mpicc:\$PATH\"" >> ~/.bashrc
echo "export PATH=\"/usr/local/lib/openmpi:\$LD_LIBRARY_PATH\"" >> ~/.bashrc
echo "export CC="/usr/local/bin/mpicc"" >> ~/.bashrc
```

#### MacOS: install OpenMPI via Homebrew
(Previous instructions recommended installing from source. Unfortunately this appears to result in a segmentation fault on `MPI_Init`. The solution is to install prebuilt binaries from Homebrew.)
```bash
brew install open-mpi
```
v5.0.0 at time of writing. Check the location of the installation using `which mpirun`; this should be something like `/opt/homebrew/bin/mpirun`. (If you see a different path, you'll need to delete or `make uninstall` previous build files manually.)

#### Test the OpenMPI installation

Compile the following example `hello_c.c` using `mpicc hello_c.c -o hello_c`:
```c
#include <stdio.h>
#include "mpi.h"

int main(int argc, char* argv[])
{
    int rank, size, len;
    char version[MPI_MAX_LIBRARY_VERSION_STRING];

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Get_library_version(version, &len);
    printf("Hello, world, I am %d of %d, (%s, %d)\n",
           rank, size, version, len);
    MPI_Finalize();

    return 0;
}
```
Then run using `mpirun -np 2 hello_c`.

### Install mpi4py (v3.1.5 at time of writing)

If needed, remove an existing installation with:
```bash
pip uninstall mpi4py
pip cache remove mpi4py
```
Then build `mpi4py` against system MPI (3.1.5 at time of writing; ignoring any existing installations or caches to use updated MPI installations):
```bash
MPICC=$(which mpicc) pip install --no-binary=mpi4py mpi4py
```
Ensure the package exists using `pip show mpi4py`. Run a test program:
```bash
mpirun -np 4 python -c "from mpi4py import MPI; print(MPI.COMM_WORLD.Get_rank())"
```
You may remove the downloaded `openmpi-*.tar.gz` and `openmpi-*` directory.

## 3. HDF5 (v1.14.3 at time of writing)

### Windows / Linux: install Parallel HDF5 from source

1. First, check for an existing HDF5 installation, using `h5cc` or `h5pcc`.
```bash
$ h5pcc -showconfig
Features:
---------
                   Parallel HDF5: yes
Parallel Filtered Dataset Writes: yes
              Large Parallel I/O: yes
              High-level library: yes
                Build HDF5 Tests: yes
                Build HDF5 Tools: yes
...
```
Otherwise, build from source using the following steps. 

2. Install `zlib` for your system (e.g. `brew install zlib` on macOS).
3. Download the [latest HDF5 source](https://www.hdfgroup.org/downloads/hdf5/source-code/), either through a browser, or through the `wget` method, and extract:
```bash
tar -xvzf hdf5-1.12.1.tar.gz
cd hdf5-1.12.1
```
4. Build HDF5 with parallel support (you will need to define `$LOCAL_DIR` again if you have re-opened the terminal):
```bash
CC=$(which mpicc) ./configure --with-zlib=$LOCAL_DIR --disable-fortran --prefix=$LOCAL_DIR --enable-shared --enable-parallel 
```
5. Make & install:
```bash
make
make check 
make install
```

#### MacOS: install Parallel HDF5 via Homebrew
```bash
brew install hdf5-mpi
```

#### Check installation

Check your installation (close and reopen terminal) with `h5pcc` as follows: 
```bash
$ h5pcc -showconfig
Features:
---------
                   Parallel HDF5: yes
Parallel Filtered Dataset Writes: yes
              Large Parallel I/O: yes
              High-level library: yes
                Build HDF5 Tests: yes
                Build HDF5 Tools: yes
...
```

## 4. h5py (master branch 4c01efa9714db40ffe27a322c4f1ba4635816e44, post-v3.10.0 at time of writing)
As before, remove any existing installation or cache using:
```bash
pip uninstall h5py
pip cache remove h5py
```
Obtain the installation point for hdf5 using `h5pcc -showconfig`:
```bash
...
General Information:
-------------------
...
  Installation point: /usr/local
...
```
Run `export HDF5_DIR=path_above` to set the environment variable for the installation point.

### Windows / Linux
Build `h5py` against `MPI` and your parallel-enabled `hdf5` installation by running.
```bash
HDF5_MPI="ON" CC=mpicc HDF5_DIR=$HDF5_DIR pip install --no-binary=h5py h5py
```
v3.10 at time of writing. 

### MacOS
Download the `master` branch: https://github.com/h5py/h5py, using `git clone https://github.com/h5py/h5py`. This is because the latest release, v3.10 at time of writing, could not be compiled.
Then, build `h5py` against `MPI` and your parallel-enabled `hdf5` installation by running:
```bash
CC="mpicc" HDF5_MPI="ON" HDF5_DIR=$HDF5_DIR pip install . --no-build-isolation
```
The `--no-build-isolation` flag is necessary to avoid re-building `mpi4py`, which would not link against the system MPI installation.

### Check installation
Finally, test the HDF5 MPI driver. Run the script `test_ph5.py` using `mpirun -np 4 python test_ph5.py`:
```python
from mpi4py import MPI
import h5py

rank = MPI.COMM_WORLD.rank 

if rank == 0:
	with h5py.File('parallel_test.hdf5', 'w') as f:
		f.create_dataset('test', (4,), dtype='i')
	print('File structure created')

MPI.COMM_WORLD.Barrier()

f = h5py.File('parallel_test.hdf5', 'a', driver='mpio', comm=MPI.COMM_WORLD)
f['test'][rank:rank+1] = rank
f.close()

print(f'Rank {rank} done')
```
This should create a file `test.h5` in the current directory. You may now remove the downloaded `h5py` directory.

## 5. Ephys2

Install git if you haven't yet.

### Clean any existing build files

```bash
rm -rf _skbuild
pip uninstall ephys2
pip cache remove ephys2
```

### Clone the ephys2 directory locally
Change directory to where you want to store the source code, then run the following and cd into that folder once it is done:
```bash
git clone https://gitlab.com/OlveczkyLab/ephys2.git
```
### Install the ephys2 dependencies
Run the following to install ephys2 dependencies before building for the first time:
```bash
pip install -r setup-requirements.txt
pip install -r gui-requirements.txt
```

### Install ephys2
#### To build in release mode:
```bash
pip install -U .
```

#### To build in developer-mode with continuous editing enabled:
```bash
python setup.py develop
```
In this case, any calls to `import ephys2` should have `src/` as the current working directory. To uninstall the developer build, do:
```bash
python setup.py develop uninstall
```

### (Optional: Synthetic benchmarks)
The synthetic benchmarks for `ephys2` come with their own (fairly large) set of dependencies, so we don't install them by default. First, install the Neuron simulator:

```bash
pip install neuron
```

(Note if on Mac M1: Python wheels for `neuron` on `arm64` don't currently exist, so you should first install it via the package from [neuron.yale.edu](https://neuron.yale.edu/neuron/download) instead of `pip`. Then, install `LFPy` and `MEArec` as below.)

```bash
pip install LFPy>=2.2.4 MEArec bmtk
```
Then, see [synthetic.md](synthetic.md) for instructions on how to generate synthetic data for benchmarks.

# Windows: accessing network drives from WSL shell
The Ubuntu shell has your Windows `C:\` drive mounted by default under `/mnt/c/`, but you will need to mount any additional drives manually.

## Map network drive in Windows

In order to mount a network drive in the Ubuntu shell, you first must map the network drive to a drive letter in Windows. 

Assuming that you already have Isilon or Lustre mounted, open Windows File Explorer and go to ***This PC***. 

At the top of the window near the toolbars, you should see a button to 'Map network drive'. Click it and select a drive letter to mount the network address to (from this point on, the instructions will assume the drive is mapped to `Z:\`).

## Mount network drive in WSL shell
First make a folder under `/mnt` corresponding to the drive you wish to mount:
```bash
sudo mkdir /mnt/z
```
\
Then edit your `fstab` file so that the shell mounts the network drive to this folder by default:

```bash
gedit /etc/fstab
```

and add the following line to the end of the file (again assuming a drive letter of `Z:\`):
```bash
Z: /mnt/z drvfs defaults 0 0
```
\
Finally, activate your fstab file from the current shell:
```bash
sudo mount -a
```
\
You can now access all of the files in your network drive in the Ubuntu shell from `/mnt/z/`. 

# Running tests
Once installed, run all tests against the build by running `pytest` as follows. Note that `pytest` is installed as a dependency in [setup.py](setup.py); otherwise, run `pip install pytest`.
```bash
python -m pytest
```
This runs tests in the [tests](tests) folder. The configuration for pytest is located at [pytest.ini](pytest.ini).

* To run tests with breakpoints (drop into debugger) upon failure, add the `--pdb` argument.
* To run tests with print statements enabled, add the `-s` argument.
* To run only the unit tests:
```bash
python -m pytest tests/unit_tests
```
* To run only the workflow (integration) tests:
```bash
python -m pytest tests/workflow_tests
```
* To run a specific unit/workflow test sequence, just give the full path:
```bash
python -m pytest tests/unit_tests/test_0_utils.py
```

## Numerical benchmarks
See [numeric_tests](numeric_tests) for a description of available numerical benchmarks.

## Performance benchmarks
See [perf_tests](perf_tests) for a description of available numerical benchmarks.

# Lint
```bash
pylint src/ephys2 
```
<!-- 
```bash
# Build & test:
git add --all .	# Run this if you've made any untracked changes
rm -rf .tox # Optional, try if the build fails
tox -e py39 # Replace with version available on your machine. This will take a few minutes the first time it's run.
```
NOTE: If you add any build-time Python dependencies (i.e. `import {...}` in `setup.py`), ensure to add this to `pyproject.toml` with the proper lower/upper bounds! -->

# Using ephys2

## Run the pipeline without parallelization:
```bash
python -m ephys2.run workflow.yaml
```
## Run the pipeline with MPI (recommended):
```bash
mpirun -np $N_PROCS python -m ephys2.run workflow.yaml
```
## Run with debug statements:
```bash
mpirun -np $N_PROCS python -m ephys2.run workflow.yaml --verbose
```
Rank 0 will print debug statements.
## Profile the pipeline's serial performance: 
```bash
python -m ephys2.run workflow.yaml --profile
``` 
This can tell you which stage of your pipeline is the bottleneck.

## Profile the pipeline's parallel performance: 
```bash
mpirun -np $N_PROCS python -m ephys2.run workflow.yaml --profile
``` 
The worker with rank `0` will print its profile upon completion. This can tell you how much time is spent in computation versus communication.

## Run the GUI
See [GUI.md](GUI.md) or simply do:
```bash
python -m ephys2.gui
```

# FAQ / Issues

**The source compiles but I get `symbol not found` errors when importing the C++ modules at runtime.**

  1. Check that your `.h` and `.cpp` files have the exact type signatures. See [this SO answer](https://stackoverflow.com/questions/39962715/expected-in-flat-namespace-error-when-importing).
  2. Check that [CMakeLists.txt](CMakeLists.txt) contains all the source `.cpp`/`.c` files.

**I get a library import error with MPI: `cannot find libimf.so` or similar.**

  You may have installed `mpi4py` without having loaded `gcc` or other dependencies on your system. With your chosen compiler configured (the above error arises when attempting to build with Intel MKL library/`icpc`, found in HPC environments, in this project we use `gcc` or `clang` exclusively) do:
```bash
pip install --upgrade --force-reinstall --no-cache-dir mpi4py
```

**I get unexpected import errors (`NameError`) during runtime.**

  Try removing the cached build files with `rm -rf _skbuild`, then `pip install -U .` again. If it persists, delete the entire package using:
	```bash
	pip show ephys2 # Get the folder path
	rm -rf PACKAGE_PATH
	```
	then reinstall the package.

**I get AttributeError: module 'sipbuild.api' has no attribute 'prepare_metadata_for_build_wheel' when building the GUI**

  This is a known issue with the PyQT build system, `sip` interacting with the Python package manager `pip`. This error is not the true one, just the one reported by `pip`. The solution is to install the relevant `qt` libraries and build tools for your system, e.g.:

  MacOS:
  ```bash
  brew install qt
  ```

  Ubuntu (20.04+):
  ```bash
  apt-get install qt5-default
  ```

# Project organization
This project follows standard PyPI format as in [example_pypi_package](https://github.com/tomchen/example_pypi_package), using a C/C++ extension build system based on [scikit-build](https://github.com/pybind/scikit_build_example) and CMake.

* [src/ephys2](src/ephys2): Python source 
* [cpp](cpp): C/C++ extensions
* [tests/unit_tests](tests/unit_tests): Unit tests
* [tests/workflow_tests](tests/workflow_tests): Workflow (end-end integration) tests
* [perf_tests](perf_tests): Performance benchmarks
* [numeric_tests](numeric_tests): Numerical accuracy tests against real & synthetic data
* [CMakeLists.txt](CMakeLists.txt): Build configuration for C/C++ source
* [setup.py](setup.py): Build configuration for Python source
* [pytest.ini](pytest.ini): Test configuration for `pytest`
* [pyproject.toml](pyproject.toml): Build-time dependencies
* [.pylintrc](.pylintrc): Lint configuration for `pylint`

# Other resources 
* See [example_pypi_package](https://github.com/tomchen/example_pypi_package) to understand other configuration files in this package. 
* See [end2end](https://github.com/artbataev/end2end) for an example of a mixed PyTorch/C++ project using `CMake` instead of `setuptools`.
* [PyTorch custom operator experiment using at::parallel_for](https://github.com/suphoff/pytorch_parallel_extension_cpp)
* [Build NumPy/SciPy with Intel® MKL](https://www.intel.com/content/www/us/en/developer/articles/technical/build-numpy-with-mkl-and-icc.html)
* https://docs.datajoint.org/python/intro/01-Data-Pipelines.html

# Future improvements / refactors
* Associate serializers more directly with individual types