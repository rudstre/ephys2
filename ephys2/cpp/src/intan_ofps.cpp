#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <fstream>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/intan_ofps.h"

namespace py = pybind11;


std::tuple<py::array_t<int64_t>, py::array_t<float>> read_intan_ofps_batch(
	const std::string &time_path,		// Path to time.dat
	const std::string &amp_path,		// Path to amplifier.dat
	const size_t start_sample,			// Start sample to read (no validation), inclusive
	const size_t stop_sample,				// Stop sample to read (no validation), non-inclusive
	const size_t n_channels				 	// Number of channels 
	)
// Read amplifier data from a Intan one-file-per-signal into NumPy arrays 
// Amplifier time is a 64-bit signed integer.
// Amplifier data is a 32-bit float in microvolts.
{
	const size_t N = stop_sample - start_sample;
	const size_t M = n_channels;

	// Read data into byte buffers
	std::byte *time_buf = new std::byte[N * 4];
	std::byte *amp_buf = new std::byte[M * N * 2];

	std::ifstream time_fin(time_path, std::ios::in | std::ios::binary);
	std::ifstream amp_fin(amp_path, std::ios::in | std::ios::binary);

	time_fin.seekg(start_sample * 4);
	amp_fin.seekg(start_sample * M * 2);

	time_fin.read((char*)time_buf, N * 4);
	amp_fin.read((char*)amp_buf, M * N * 2);

	// Parse data from buffer into array
	int64_t *time_data = new int64_t[N];	// Time
	float *amp_data = new float[M * N]; 	// Amplifier data in row-major ordering per NumPy convention
	size_t time_buf_i = 0;
	size_t amp_buf_i = 0;
	size_t time_i = 0;
	size_t amp_i = 0;

	for (size_t sample_i=0; sample_i<N; sample_i++) {
		time_data[time_i] = (int64_t) (*(int32_t*) &time_buf[time_buf_i]);
		time_buf_i+=4;
		time_i++;
		for (size_t channel_i=0; channel_i<M; channel_i++) {
			amp_data[amp_i] = 0.195 * ((float) (*(int16_t*) &amp_buf[amp_buf_i])); // Convert 16-bit ADC sample to microvolts
			amp_buf_i+=2;
			amp_i++;
		}
	}

	delete[] time_buf;
	delete[] amp_buf;

	return std::tuple(
		arr2numpy(time_data, {N}), 
		arr2numpy(amp_data, {N, M})
	); 
}
