#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <fstream>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/rhd2000.h"

namespace py = pybind11;


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
	) 
// Read amplifier data from an RHD file into a NumPy array
// Amplifier time is a 64-bit signed integer.
// Amplifier data is a 32-bit float in microvolts.
{
	py_assert(start_sample >= 0, "start_sample must be nonnegative");
	py_assert(stop_sample >= 0, "stop_sample must be nonnegative");
	py_assert(start_sample <= stop_sample, "stop_sample cannot occur before start_sample");

	const size_t start_block = start_sample / samples_per_block;
	const size_t start_offset = start_sample % samples_per_block;
	const size_t stop_block = (stop_sample / samples_per_block) + 1;
	const size_t stop_offset = stop_sample % samples_per_block;
	const size_t N = stop_sample - start_sample;
	const size_t M = n_channels;
	const size_t Ma = n_analog_channels;
	const size_t Md = digital_in_enabled ? 1 : 0;
	const size_t analog_digital_byte_gap = bytes_after_amp - (Md * 2) * samples_per_block - 2 * Ma * (samples_per_block / 4);

	py_assert(start_block < stop_block, "Start block must occur before stop block");

	const size_t n_blocks = (stop_block - start_block);
	const size_t buf_size = n_blocks * bytes_per_block;
	const size_t buf_offset = header_offset + start_block * bytes_per_block;

	// Read blocks into byte buffer
	std::byte *buffer = new std::byte[buf_size];
	std::ifstream fin(filepath, std::ios::in | std::ios::binary);
	fin.seekg(buf_offset);
	fin.read((char*)buffer, buf_size);

	// Parse data from buffer into arrays
	int64_t *amp_t = new int64_t[N];					// Time
	float *amp_data = new float[M * N]; 			// Amplifier data in row-major ordering per NumPy convention
	float *analog_data = new float[Ma * N];  	// Analog aux input data
	bool *digital_data = new bool[Md * N]; 		// Digital aux input data

	// State
	size_t buf_i = 4 * start_offset; 				// Skip start offset for time
	size_t old_buf_i = 0;
	size_t amp_t_i = 0;
	size_t amp_i = 0;
	size_t analog_i = 0;
	size_t digital_i = 0;
	size_t sample_i_start = start_offset;
	size_t sample_i_stop = samples_per_block;
	float analog_value = 0;

	for (size_t block_i=0; block_i<n_blocks; block_i++) {
		sample_i_stop = (block_i == n_blocks-1) ? stop_offset : samples_per_block;

		// Read time
		for (size_t sample_i=sample_i_start; sample_i<sample_i_stop; sample_i++) {
			amp_t[amp_t_i] = (int64_t) (*(int32_t*) &buffer[buf_i]);
			amp_t_i++;
			buf_i += 4;
		}

		buf_i += (samples_per_block - sample_i_stop) * 4; // Skip stop offset for time

		// Read amplifier
		for (size_t channel_i=0; channel_i<M; channel_i++) { // RHD stores each block in column-major order
			buf_i += sample_i_start * 2; // Skip start offset for this channel
			for (size_t sample_i=sample_i_start; sample_i<sample_i_stop; sample_i++) {
				amp_i = (block_i * samples_per_block + sample_i - start_offset) * M + channel_i; // Convert column-major RHD to row-major NumPy index
				amp_data[amp_i] = 0.195 * ((float) (*(uint16_t*) &buffer[buf_i]) - 32768); // Convert 16-bit ADC input to microvolts
				buf_i += 2;
			}
			buf_i += (samples_per_block - sample_i_stop) * 2; // Skip stop offset for channel
		}

		old_buf_i = buf_i;

		// Read analog in (sampled at 1/4 the rate; we repeat values in the output to maintain temporal consistency)
		if (Ma > 0) {
			for (size_t channel_i=0; channel_i<Ma; channel_i++) {
				for (size_t sample_i=0; sample_i<samples_per_block; sample_i++) {
					// Advance buf_i at 1/4 the speed
					if (sample_i % 4 == 0) {
						analog_value = 0.0000374 * ((float) (*(uint16_t*) &buffer[buf_i]));  // Convert 16-bit aux ADC input to volts
						buf_i += 2;
					}
					// Write analog value at full speed
					if ((sample_i >= sample_i_start) && (sample_i < sample_i_stop)) {
						analog_i = (block_i * samples_per_block + sample_i - start_offset) * Ma + channel_i;
						analog_data[analog_i] = analog_value;
					}
				}
			}
		}

		buf_i += analog_digital_byte_gap; // Skip offset between analog and digital data, if they exist

		// Read digital in
		if (Md > 0) {
			buf_i += sample_i_start * 2; // Skip start offset for digital inputs
			for (size_t sample_i=sample_i_start; sample_i<sample_i_stop; sample_i++) {
				digital_data[digital_i] = *(uint16_t*) &buffer[buf_i];
				digital_i++;
				buf_i += 2;
			}
			buf_i += (samples_per_block - sample_i_stop) * 2;  // Skip stop offset for digital inputs
			py_assert(digital_i == amp_t_i, "Digital index data inconsistent");
		}

		py_assert(old_buf_i + bytes_after_amp == buf_i, "Inconsistent index after reading aux data");
		sample_i_start = 0; // Reset start offset after the first block has been read
	}

	delete[] buffer;

	// All outputs are temporally aligned
	return std::tuple(
		arr2numpy(amp_t, {N}),
		arr2numpy(amp_data, {N, M}),
		arr2numpy(analog_data, {N, Ma}),
		arr2numpy(digital_data, {N})
	);
}
