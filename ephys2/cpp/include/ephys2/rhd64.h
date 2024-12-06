#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef RHD64_H
#define RHD64_H

namespace py = pybind11;

using RHD64Data = std::tuple<
	py::array_t<int64_t>, 		// Recorded time
	py::array_t<float>,			// Amplifier data
	py::array_t<float>, 		// Accelerometer inputs
	py::array_t<uint16_t> 		// Digital inputs
>;

RHD64Data read_rhd64_batch(
	const std::string &filepath,		// Source filepath
	const size_t start_sample,			// Start sample to read (no validation), inclusive
	const size_t stop_sample				// Stop sample to read (no validation), non-inclusive
	);

#endif