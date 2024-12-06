#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/snippet.h"

namespace py = pybind11;

SnippetData snippet_channel_groups(
	py::array_t<int64_t> amp_t, 		// Amplifier time N samples 
	py::array_t<float> amp_data, 		// Amplifier data N samples x M channels
	const size_t s_length, 					// Snippet length
	const float hi_thr,							// Detection threshold
	const float lo_thr,							// Return threshold
	const size_t return_n,					// Minimum return time
	const size_t n_channels 				// Number of channels per channel group
	)
// Detect & snippet spikes on a per-channel group basis (assumes channel groups are contiguous groups of 4 channels)
{
	py_assert(hi_thr > 0, "hi_thr must be positive");
	py_assert(lo_thr > 0, "hi_thr must be positive");

	auto data = amp_data.unchecked<2>(); // Check that the array has 2 dimensions; don't copy underlying data
	auto time = amp_t.unchecked<1>(); // Similarly
	const size_t N = data.shape(0);
	const size_t M = data.shape(1);

	py_assert(M % n_channels == 0, "snippet_channel_groups did not receive a whole number of channel groups"); // Ensure that there are a whole number of channel groups in the data

	const size_t T = (size_t) M / n_channels; // Number of channel groups

	// The following implements the state machine from Figure 2
	
	// State
	std::vector<bool> detected(T, false);		// Detected state
	std::vector<size_t> returned(T, 0); 		// Number of consecutive samples below return threshold
	std::vector<float> peak_vals(T, 0.0);		// Current peak value
	std::vector<int64_t> peak_times(T, 0);	// Current peak times

	// Results
	std::vector<std::vector<int64_t>> group_times(T, std::vector<int64_t>()); 	// Peak times of detected waveforms in each group
	std::vector<std::vector<float>> group_snippets(T, std::vector<float>()); 		// Detected waveforms in row-major order for each group

	const size_t snip_left = (int) s_length / 2;
	const size_t snip_right = s_length - snip_left;

	for (size_t sample_i=0; sample_i<N; sample_i++) {
		for (size_t T_i=0; T_i<T; T_i++) {
			const size_t C_g = T_i * n_channels; // Start channel of current group
			// Currently in a detected state for this channel group
			if (detected[T_i]) {
				bool below = true;
				float max = 0.0;
				for (size_t chan_i=C_g; chan_i<C_g+n_channels; chan_i++) {
					float val = std::abs(data(sample_i, chan_i));
					below = below && (val < lo_thr);
					max = std::max(max, val);
				}
				// Update peak
				if (max > peak_vals[T_i]) {
					peak_vals[T_i] = max;
					peak_times[T_i] = sample_i;
				}
				// Return threshold is crossed by all channels
				if (below) {
					returned[T_i]++;
					if (returned[T_i] >= return_n) {
						auto peak_i = peak_times[T_i];
						// Take the snippet up to left/right boundaries
						if (peak_i > snip_left-1 && 
								peak_i < N - snip_right) {
							for (size_t c_i=C_g; c_i<C_g+n_channels; c_i++) {
								for (size_t w_i=peak_i-snip_left; w_i<peak_i+snip_right; w_i++) { // Store waveform in row-major order
									group_snippets[T_i].push_back(data(w_i, c_i));
								}
							}
							group_times[T_i].push_back(time(peak_i));
						} 
						// Reset state to undetected
						detected[T_i] = false;
						returned[T_i] = 0;
						peak_vals[T_i] = 0.0;
					}
				// Not crossed, reset the return counter
				} else {
					returned[T_i] = 0;
				}
			// Not in a detected state
			} else {
				bool above = false;
				float max = 0.0;
				for (size_t chan_i=0; chan_i<n_channels; chan_i++) {
					float val = std::abs(data(sample_i, C_g + chan_i));
					above = above || (val > hi_thr);
					max = std::max(max, val);
				}
				// Detection threshold crossed by any channel
				if (above) {
					// Set state to detected
					detected[T_i] = true;
					peak_vals[T_i] = max;
					peak_times[T_i] = sample_i;
				}
			}
		}
	}

	std::vector<py::array_t<int64_t>> py_group_times(T);
	std::vector<py::array_t<float>> py_group_snippets(T);
	size_t max_len = 0;
	for (size_t i=0; i<T; i++) {
		const size_t s_N = group_times[i].size();
		py_group_times[i] = seq2numpy(group_times[i], {s_N});
		py_group_snippets[i] = seq2numpy(group_snippets[i], {s_N, n_channels*s_length});
		max_len = std::max(max_len, s_N);
	}

	return {
		py_group_times,
		py_group_snippets,
		max_len
	};
}