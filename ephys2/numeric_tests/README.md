# Numerical benchmarks of spike-sorting stages.

The following commands should be run from this folder.

First, ensure you have a working `ephys2` installation, per the [developer docs](..). Install the benchmarking dependencies using 
```
pip install -r requirements.txt
```
Then, run any of the modules as python scripts using 
```bash
python -m clustering.circles # Runs clustering benchmark on 2d synthetic "circles dataset"
```
These scripts do not have a structure to them like the unit tests; they may open windows, print to the terminal, etc. Check each respective module for its documentation.