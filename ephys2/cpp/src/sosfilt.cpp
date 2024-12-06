#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "../include/ephys2/sosfilt.h"

namespace py = pybind11;

void sosfiltfilt2d(
	py::array_t<float> sos, // Second-order sections 						(n_sections x 6)
	py::array_t<float> zi, 	// Initial conditions 							(n_sections x 2)
	py::array_t<float> x,		// Data array (modified in-place)		(n_samples x n_channels)
	int pad_type, 					// Padding type: 0 is odd, 1 is even
	size_t pad_len					// Padding length
	)
// Second-order sections forward-backward IIR filter 
// C++ version of Scipy implementation, https://github.com/scipy/scipy/blob/v1.7.1/scipy/signal/signaltools.py
{
	auto sos_data = sos.unchecked<2>();
	auto zi_data = zi.unchecked<2>();
	auto x_data = x.mutable_unchecked<2>();

	const size_t N = x_data.shape(0);
	const size_t M = x_data.shape(1);
	const size_t N_sections = sos_data.shape(0);

	assert(N > pad_len);

	int sgn = 1;
	switch(pad_type) {
		case 0:
			// Odd padding type
			sgn = -1;
			break;
		case 1:
			// Even padding type
			sgn = 1;
			break;
		default:
			throw std::invalid_argument("pad_type should be 'odd' or 'even'");
	}

	float l_ext[pad_len][M]; // Left signal extension
	float r_ext[pad_len][M]; // Right signal extension
	float zi_state[M][N_sections][2]; // Zi

	// Initialize left and right extensions
	for (int c=0; c<M; c++) {
		for (int i=0; i<pad_len; i++) {
			l_ext[pad_len-i-1][c] = x_data(i, c) * sgn;
			r_ext[i][c] = x_data(N-i-1, c) * sgn;
		}
	}

	// Forward pass

	// Initialize zi state
	for (int s=0; s<N_sections; s++) {
		for (int c=0; c<M; c++) {
			zi_state[c][s][0] = zi_data(s,0) * l_ext[0][c];
			zi_state[c][s][1] = zi_data(s,1) * l_ext[0][c];
		}
	}

	for (int c=0; c<M; c++) {
		for (int i=0; i<pad_len; i++) {
			for (int s=0; s<N_sections; s++) {
				const float x_i = l_ext[i][c];
				l_ext[i][c] = sos_data(s, 0) * x_i + zi_state[c][s][0];
				zi_state[c][s][0] = sos_data(s, 1) * x_i - sos_data(s, 4) * l_ext[i][c] + zi_state[c][s][1];
				zi_state[c][s][1] = sos_data(s, 2) * x_i - sos_data(s, 5) * l_ext[i][c];
			}
		}
	}

	for (int c=0; c<M; c++) {
		for (int i=0; i<N; i++) {
			for (int s=0; s<N_sections; s++) {
				const float x_i = x_data(i,c);
				x_data(i,c) = sos_data(s, 0) * x_i + zi_state[c][s][0];
				zi_state[c][s][0] = sos_data(s, 1) * x_i - sos_data(s, 4) * x_data(i,c) + zi_state[c][s][1];
				zi_state[c][s][1] = sos_data(s, 2) * x_i - sos_data(s, 5) * x_data(i,c);
			}
		}
	}

	for (int c=0; c<M; c++) {
		for (int i=0; i<pad_len; i++) {
			for (int s=0; s<N_sections; s++) {
				const float x_i = r_ext[i][c];
				r_ext[i][c] = sos_data(s, 0) * x_i + zi_state[c][s][0];
				zi_state[c][s][0] = sos_data(s, 1) * x_i - sos_data(s, 4) * r_ext[i][c] + zi_state[c][s][1];
				zi_state[c][s][1] = sos_data(s, 2) * x_i - sos_data(s, 5) * r_ext[i][c];
			}
		}
	}

	// Backward pass

	// Initialize zi state
	for (int s=0; s<N_sections; s++) {
		for (int c=0; c<M; c++) {
			zi_state[c][s][0] = zi_data(s,0) * r_ext[pad_len-1][c];
			zi_state[c][s][1] = zi_data(s,1) * r_ext[pad_len-1][c];
		}
	}

	for (int c=0; c<M; c++) {
		for (int i=pad_len-1; i>=0; i--) {
			for (int s=0; s<N_sections; s++) {
				const float x_i = r_ext[i][c];
				r_ext[i][c] = sos_data(s, 0) * x_i + zi_state[c][s][0];
				zi_state[c][s][0] = sos_data(s, 1) * x_i - sos_data(s, 4) * r_ext[i][c] + zi_state[c][s][1];
				zi_state[c][s][1] = sos_data(s, 2) * x_i - sos_data(s, 5) * r_ext[i][c];
			}
		}
	}

	for (int c=0; c<M; c++) {
		for (int i=N-1; i>=0; i--) {
			for (int s=0; s<N_sections; s++) {
				const float x_i = x_data(i,c);
				x_data(i,c) = sos_data(s, 0) * x_i + zi_state[c][s][0];
				zi_state[c][s][0] = sos_data(s, 1) * x_i - sos_data(s, 4) * x_data(i,c) + zi_state[c][s][1];
				zi_state[c][s][1] = sos_data(s, 2) * x_i - sos_data(s, 5) * x_data(i,c);
			}
		}
	}
}