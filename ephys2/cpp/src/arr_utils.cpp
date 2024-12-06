#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "../include/ephys2/utils.h"

namespace py = pybind11;

std::vector<size_t> calc_strides(size_t *shape, size_t size, size_t ndim)
// Calculate array strides from shape and dtype size
{
	size_t *strides = new size_t[ndim];
	int stride = size;
	strides[ndim-1] = stride;
	for (size_t i=ndim-1; i>1; i--) {
		stride *= shape[i];
		strides[i-1] = stride;
	}
	return std::vector<size_t>(strides, strides + ndim);
}