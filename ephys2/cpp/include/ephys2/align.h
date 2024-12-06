#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef ALIGN_H
#define ALIGN_H

namespace py = pybind11;

py::array_t<int64_t> align_sequences(
	py::array_t<int64_t> times1, 				// Times from input sequence 1 
	py::array_t<int64_t> times2, 				// Times from input sequence 2
	py::array_t<int64_t> vals1, 				// Values from input sequence 1 
	py::array_t<int64_t> vals2, 				// Values from input sequence 2 
	const size_t max_dist, 							// Maximum temporal distance for alignment
	const int64_t fill_value 						// Fill value for un-aligned data
	);

std::tuple<std::vector<size_t>, std::vector<size_t>> pair_sequences(
		int64_t* times1,
		int64_t* times2,
		size_t N1,
		size_t N2,
		const size_t max_dist
	);

void mergesort_into(
		std::vector<int64_t>& vals, 	// Implicit 2xN value vector to modify
		int64_t* times1,
		int64_t* times2,
		int64_t* vals1,
		int64_t* vals2,
		size_t i1,										// Start index for seq 1
		size_t i2,										// Start index for seq 2
		const size_t I1,							// Stop index for seq 1
		const size_t I2,							// Stop index for seq 2
		const int64_t fill_value
	);

#endif