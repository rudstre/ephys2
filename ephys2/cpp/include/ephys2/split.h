#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "./link.h"

#ifndef SPLIT_H
#define SPLIT_H

namespace py = pybind11;

using LabelMap = std::unordered_map<int64_t, int64_t>;

LabelMap split_block_1d(
	py::array_t<int64_t> block_labels, 										// Labels in the block being split at the index (will be written to)
	const int block_start, 																// Starting index of the block
	const int block_end, 																	// Ending index of the block
	const int index, 																			// Index at which to split the block (relative to 0, not block_start); also determines which label to split
	const int64_t label,																	// Label to split
	EVIncidence linkage,																	// Linkage matrix
	const std::unordered_set<int64_t>& preserved_indices 	// Indices which should not be re-labeled
);

LabelMap split_blocks_2d(
	py::array_t<int64_t> labels, 							// Labels in the blocks being split (written to)
	const int blocks_start, 									// Start index of the blocks
	const int blocks_end, 										// End index of the blocks
	const int block_size, 										// Size of the block
	const std::unordered_set<int>& indices, 	// Labels to exclude from the split
	const int64_t label, 											// Label to split
	EVIncidence linkage												// Linkage matrix (written to)
);

std::optional<int64_t> find_next_label(
	py::array_t<int64_t> labels,  // Labels within which to search
	const int index_start,				// Start index within the labels array
	const int index_end,					// End index within the labels array
	const int block_start,				// Start index of the block
	const int block_end						// End index of the block
);

void relabel(
	py::array_t<int64_t> labels, 													// Labels (written to)
	const std::unordered_map<int64_t, int64_t>& label_map // Map from old labels to new labels
);

#endif
