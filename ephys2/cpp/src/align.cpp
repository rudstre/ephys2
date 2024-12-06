#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/align.h"

namespace py = pybind11;

py::array_t<int64_t> align_sequences(
	py::array_t<int64_t> times1, 				// Times from input sequence 1 
	py::array_t<int64_t> times2, 				// Times from input sequence 2
	py::array_t<int64_t> vals1, 				// Values from input sequence 1 
	py::array_t<int64_t> vals2, 				// Values from input sequence 2 
	const size_t max_dist, 							// Maximum temporal distance for alignment
	const int64_t fill_value 						// Fill value for un-aligned data
	)
// Align two sequences in time, filling in missing data as-needed.
{
	py_assert(max_dist >= 0, "Maximum distance must be nonnegative");

	const size_t N1 = times1.shape(0);
	const size_t N2 = times2.shape(0);

	int64_t* ts1 = static_cast<int64_t *>(times1.request().ptr);
	int64_t* ts2 = static_cast<int64_t *>(times2.request().ptr);
	int64_t* vs1 = static_cast<int64_t *>(vals1.request().ptr);
	int64_t* vs2 = static_cast<int64_t *>(vals2.request().ptr);

	// Pair the sequences
	auto paired_indices = pair_sequences(ts1, ts2, N1, N2, max_dist);
	std::vector<size_t> idxs1 = std::get<0>(paired_indices);
	std::vector<size_t> idxs2 = std::get<1>(paired_indices);
	py_assert(idxs1.size() == idxs2.size(), "Index sizes were inconsistent");
	const size_t K = idxs1.size();

	// Fill in values & missing values
	std::vector<int64_t> vals; // Values from the full aligned sequence (N x 2)
	size_t i1 = 0;
	size_t i2 = 0;
	for (int k=0; k<K; k++) {
		size_t I1 = idxs1[k];
		size_t I2 = idxs2[k];
		mergesort_into(vals, ts1, ts2, vs1, vs2, i1, i2, I1, I2, fill_value);
		vals.push_back(vs1[I1]);
		vals.push_back(vs2[I2]);
		i1 = I1 + 1;
		i2 = I2 + 1;
	}
	mergesort_into(vals, ts1, ts2, vs1, vs2, i1, i2, N1, N2, fill_value);

	// Reshape result
	size_t N = vals.size() / 2;
	return seq2numpy(vals, {N, 2});
}

std::tuple<std::vector<size_t>, std::vector<size_t>> pair_sequences(
		int64_t* times1,
		int64_t* times2,
		size_t N1,
		size_t N2,
		const size_t max_dist
	)
// Find an index pairing between two sequences satisfying the maximum distance criterion.
{
	py_assert(max_dist > 0, "Maximum distance must be positive");

	bool reverse_args = false;
	if (N2 < N1) {
		// Reverse arguments. WLOG, we assume the first is smaller than the second.
		std::swap(times1, times2);
		std::swap(N1, N2);
		reverse_args = true;
	}

	std::vector<size_t> idxs1;
	std::vector<size_t> idxs2;

	size_t i1 = 0;
	size_t i2 = 0;

	while ((i1 < N1) && (i2 < N2)) {
		size_t best_dist = std::abs(times1[i1] - times2[i2]);
		size_t best_i2 = i2;

		while ((i2 < N2) && (times2[i2] <= times1[i1])) {
			size_t dist = std::abs(times1[i1] - times2[i2]);
			if (dist < best_dist) {
				best_dist = dist;
				best_i2 = i2;
			}
			i2++;
		}

		if ((best_i2 < N2) && (best_dist <= max_dist)) {
			idxs1.push_back(i1);
			idxs2.push_back(best_i2);
		}

		i1++;
		i2 = best_i2 + 1;
	}

	if (reverse_args) return {idxs2, idxs1};
	else return {idxs1, idxs2};
}

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
	)
// Merge-sort two timestamped arrays between a pair of indices into an output.
{
	while ((i1 < I1) && (i2 < I2)) {
		if (times1[i1] <= times2[i2]) {
			// First won
			vals.push_back(vals1[i1]);
			vals.push_back(fill_value);
			i1++;
		} else {
			// Second one
			vals.push_back(fill_value);
			vals.push_back(vals2[i2]);
			i2++;
		}
	}

	while (i1 < I1) {
		vals.push_back(vals1[i1]);
		vals.push_back(fill_value);
		i1++;
	}

	while (i2 < I2) {
		vals.push_back(fill_value);
		vals.push_back(vals2[i2]);
		i2++;
	}
}


