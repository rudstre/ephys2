# Ephys2 C++ source
This C++ project exists to accelerate operations on NumPy arrays, and can be built and tested independently.

## Build

```bash
cd build
cmake ..
make
make install
```

## Test

```bash
cd tests/build
cmake ..
make
cd ../bin
./my_test_exe # Replace with test file
```

# References
* [A look at the performance of expression templates in C++: Eigen vs Blaze vs Fastor vs Armadillo vs XTensor](https://romanpoya.medium.com/a-look-at-the-performance-of-expression-templates-in-c-eigen-vs-blaze-vs-fastor-vs-armadillo-vs-2474ed38d982)
* [OpenGL mathematics](https://github.com/g-truc/glm)
* https://stackoverflow.com/questions/60915627/is-pybind11-pyarray-object-thread-safe
* https://medium.com/analytics-vidhya/beating-numpy-performance-by-extending-python-with-c-c9b644ee2ca8
* https://stackoverflow.com/questions/3572580/python-and-openmp-c-extensions
* https://stackoverflow.com/questions/13839358/extending-python-with-parallelized-c-programs-under-omp
* https://stackoverflow.com/questions/59695831/pybind11-accessing-python-object-with-openmp-using-for-loop
http://crail.incubator.apache.org/blog/2019/01/python.html
* https://stackoverflow.com/questions/21866422/writing-to-file-with-cython-parallel-parallel-and-nogil
http://www.code-corner.de/?p=183
* https://stackoverflow.com/questions/54793539/pybind11-modify-numpy-array-from-c
* https://www.linyuanshi.me/post/pybind11-array/
* https://pybind11.readthedocs.io/en/stable/advanced/pycpp/numpy.html
* https://pybind11.readthedocs.io/en/stable/advanced/cast/eigen.html
* https://stackoverflow.com/questions/50878901/pybind11-vs-numpy-for-a-matrix-product
* https://github.com/pybind/cmake_example