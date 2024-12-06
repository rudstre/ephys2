#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef DETECT_H
#define DETECT_H

namespace py = pybind11;

py::array_t<int64_t> detect_channel(
	py::array_t<int64_t> amp_t, 		// Amplifier time N samples 
	py::array_t<float> amp_data, 		// Amplifier data N samples for single channel
	const float thr,								// Detection threshold
	const size_t refr								// Refractory period
	);

#endif