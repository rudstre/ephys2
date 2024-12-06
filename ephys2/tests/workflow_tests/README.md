# Workflow tests

These "workflow tests", better referred to as _integration tests_, simulate the entire `ephys2` pipeline end-end from the perspective of a user, by running specific configuration files. 

The goal of these tests is _not_ to guarantee numerical accuracy, but rather:
- ensure that stages and workflows composed of multiple stages execute without exceptions
- ensure that certain workflows always result in a ground-truth output which is known
- 

For numerical accuracy tests, see the `numeric-tests` folder in the outer source folder.