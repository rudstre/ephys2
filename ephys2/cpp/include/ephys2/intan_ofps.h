#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef INTAN_OFPS_H
#define INTAN_OFPS_H

namespace py = pybind11;

std::tuple<py::array_t<int64_t>, py::array_t<float>> read_intan_ofps_batch(
	const std::string &time_path,		// Path to time.dat
	const std::string &amp_path,		// Path to amplifier.dat
	const size_t start_sample,			// Start sample to read (no validation), inclusive
	const size_t stop_sample,				// Stop sample to read (no validation), non-inclusive
	const size_t n_channels				 	// Number of channels 
	);

#endif