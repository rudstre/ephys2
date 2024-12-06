#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef SNIPPET_H
#define SNIPPET_H

namespace py = pybind11;

using SnippetData = std::tuple<
	std::vector<py::array_t<int64_t>>, 	// Group times
	std::vector<py::array_t<float>>, 		// Group snippets
	size_t															// Maximum length
>;

SnippetData snippet_channel_groups(
	py::array_t<int64_t> amp_t, 		// Amplifier time N samples 
	py::array_t<float> amp_data, 		// Amplifier data N samples x M channels
	const size_t s_length, 					// Snippet length
	const float hi_thr,							// Detection threshold
	const float lo_thr,							// Return threshold
	const size_t return_n,					// Minimum return time
	const size_t n_channels 				// Number of channels per channel group
	);

#endif