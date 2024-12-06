#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <fstream>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/rhd64.h"

namespace py = pybind11;


RHD64Data read_rhd64_batch(
	const std::string &filepath,		// Source filepath
	const size_t start_sample,			// Start sample to read (no validation), inclusive
	const size_t stop_sample				// Stop sample to read (no validation), non-inclusive
	)
// Read amplifier data from an FAST-format RHD file into a NumPy array 
// See https://github.com/Olveczky-Lab/FAST/blob/master/RHDFormat.txt for the data format details.
// Amplifier time is a 64-bit signed integer.
// Amplifier data is a 32-bit float in microvolts.
// There are a fixed number of 64 channels.
{
	py_assert(start_sample <= stop_sample, "Stop sample cannot occur before start sample");

	const size_t N = stop_sample - start_sample; // No. samples
	const size_t N_chips = 2; // No. chips
	const size_t C = 32; // No. channels per chip
	const size_t M = N_chips * C; // No. total channels
	const size_t bytes_per_sample = 176;
	const size_t Ma = 3; // No. acc channels

	const size_t buf_size = N * bytes_per_sample;
	const size_t buf_offset = start_sample * bytes_per_sample;

	// Read block into byte buffer
	std::byte *buffer = new std::byte[buf_size];
	std::ifstream fin(filepath, std::ios::in | std::ios::binary);
	fin.seekg(buf_offset);
	fin.read((char*)buffer, buf_size);

	// Parse data from buffer into array
	int64_t *amp_t = new int64_t[N];			// Time
	float *amp_data = new float[M * N]; 		// Amplifier data in row-major ordering per NumPy convention
	float *acc_data = new float[Ma * N];  		// Accelerometer inputs
	float *acc_buffer = new float[Ma];			// Accelerometer buffer
	uint16_t *digital_data = new uint16_t[N]; 	// Digital inputs
	size_t buf_i = 0; 			
	size_t amp_t_i = 0;
	size_t amp_i = 0;
	size_t acc_i = 0; 						// Accelerometer sample index
	size_t quad_i = start_sample % 4; 		// (Absolute) quadrature sample index (0-3); used for reading acc data
	bool acc_started = quad_i == 1; 		// Whether the first complete acc triplet can be read

	// Inner loop indices
	size_t buf_i_chip = 0;
	size_t buf_i_chan = 0;

	for (size_t sample_i=0; sample_i<N; sample_i++) {
		// Skip header
		buf_i += 8; 
		// Read timestamp
		amp_t[amp_t_i] = (int64_t) (*(int32_t*) &buffer[buf_i]); 
		amp_t_i++;
		buf_i += 4;
		// Skip unused
		buf_i += 4;
		// Skip VDD, temp
		buf_i += 2;
		// Read acc 
		// (the three channels are interleaved through the samples, going NONE-CH1-CH2-CH3-NONE-CH1-CH2-CH3... with NONE to be skipped)
		if (quad_i > 0 && // Skip the NONE
			acc_started) // To avoid reading partial triplets, wait until the first complete triplet appears
		{ 
			acc_buffer[quad_i - 1] = 3.74e-5 * (((float) (*(uint16_t*) &buffer[buf_i])) - 32768);
			while ((quad_i == 3) && (acc_i < sample_i)) {
				// Backfill acc data when acc buffer is full
				for (int i=0; i<Ma; i++) {
					acc_data[acc_i * Ma + i] = acc_buffer[i];
				}
				acc_i++;
			}
		}
		buf_i += 2;
		// Skip unused
		buf_i += 4;
		// Read amplifier channels
		for (size_t chip_i=0; chip_i<N_chips; chip_i++) {
			buf_i_chip = buf_i + chip_i * 2; 
			for (size_t channel_i=0; channel_i<C; channel_i++) {
				// Read data from this chip (channels across chips are interleaved)
				buf_i_chan = buf_i_chip + channel_i * N_chips * 2; 
				// Convert 16-bit ADC sample to microvolts
				amp_data[amp_i] = 0.195 * ((float) (*(uint16_t*) &buffer[buf_i_chan]) - 32768); 
				// Advance in row-major order
				amp_i++;
			}
		}
		// Finished reading amplifier data
		buf_i += 2 * M;
		// Skip unused 
		buf_i += 20;
		// Read digital in
		digital_data[sample_i] = *(uint16_t*) &buffer[buf_i];
		buf_i += 4;
		quad_i = (quad_i + 1) % 4;
		acc_started = acc_started || (quad_i == 1); 
	}

	delete[] buffer;
	delete[] acc_buffer;

	return std::tuple(
		arr2numpy(amp_t, {N}), 
		arr2numpy(amp_data, {N, M}),
		arr2numpy(acc_data, {N, Ma}),
		arr2numpy(digital_data, {N})
	); 
}
