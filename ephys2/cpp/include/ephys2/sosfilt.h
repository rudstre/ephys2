#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef SOSFILT_H
#define SOSFILT_H

namespace py = pybind11;

void sosfiltfilt2d(
	py::array_t<float> sos, // Second-order sections 						(n_sections x 6)
	py::array_t<float> zi, 	// Initial conditions 							(n_sections x 2)
	py::array_t<float> x,		// Data array (modified in-place)		(n_samples x n_channels)
	int pad_type, 					// Padding type: 0 is odd, 1 is even
	size_t pad_len					// Padding length
	);

#endif