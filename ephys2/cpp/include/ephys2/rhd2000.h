#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef RHD2000_H
#define RHD2000_H

namespace py = pybind11;

using RHD2000Data = std::tuple<
	py::array_t<int64_t>, 			// Recorded time
	py::array_t<float>, 			// Amplifier data
	py::array_t<float>, 			// Analog inputs
	py::array_t<uint16_t> 			// Digital inputs
>;

RHD2000Data read_rhd2000_batch(
	const std::string &filepath,
	const size_t header_offset, 		// Byte offset of header data
	const size_t bytes_per_block, 	// Bytes per RHD data block
	const size_t bytes_after_amp, 	// Bytes after amplifier data in each block
	const size_t samples_per_block, // Samples per RHD data block
	const size_t start_sample,			// Start sample to read (no validation), inclusive
	const size_t stop_sample,				// Stop sample to read (no validation), non-inclusive
	const size_t n_channels,				// Number of channels 
	const size_t n_analog_channels, // Number of aux analog in channels
	const bool digital_in_enabled   // Whether aux digital in channels are enabled
	);

#endif