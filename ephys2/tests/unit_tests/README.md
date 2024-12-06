# Unit tests

These are tests intended to assert pass/fail properties of individual stages in ephys2 using [pytest](https://docs.pytest.org/en/6.2.x/). Run `python -m pytest` from the root Python package directory. 

These tests are intended to be run against an existing `ephys2` installation.

## Adding new tests

* Prepend an integer `N_` to specify the test order. Generally prefer to test sub-components before super-components.