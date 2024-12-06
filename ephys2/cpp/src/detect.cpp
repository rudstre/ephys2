#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/detect.h"

namespace py = pybind11;

py::array_t<int64_t> detect_channel(
	py::array_t<int64_t> amp_t, 		// Amplifier time N samples 
	py::array_t<float> amp_data, 		// Amplifier data N samples for single channel
	const float thr,								// Detection threshold
	const size_t refr								// Refractory period
	)
// Detect spikes in a single channel with refractory period
{
	assert(thr > 0);
	assert(refr >= 0);

	auto data = amp_data.unchecked<1>(); 
	auto time = amp_t.unchecked<1>(); 
	const size_t N = data.shape(0);

	// State
	bool detected = false;
	int64_t since_detected = 0;

	// Results
	std::vector<int64_t> detected_times; // Times of detected events

	for (size_t sample_i=0; sample_i<N; sample_i++) {
		// Currently in a detected state 
		if (detected) {
			since_detected++;
			if (since_detected > refr) {
				detected = false;
				since_detected = 0;
			}
		// Not in a detected state
		} else {
			if (std::abs(data(sample_i)) > thr) {
				detected = true;
				detected_times.push_back(time(sample_i));
			}
		}
	}

	return seq2numpy(detected_times, {detected_times.size()});
}