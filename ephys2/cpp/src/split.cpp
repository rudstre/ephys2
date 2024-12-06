#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/split.h"
#include "../include/ephys2/link.h"

LabelMap split_block_1d(
	py::array_t<int64_t> block_labels, 										// Labels in the block being split at the index (will be written to)
	const int block_start, 																// Starting index of the block
	const int block_end, 																	// Ending index of the block
	const int index, 																			// Index at which to split the block (relative to 0, not block_start); also determines which label to split
	const int64_t label,																	// Label to split
	EVIncidence linkage,																	// Linkage matrix
	const std::unordered_set<int64_t>& preserved_indices 	// Indices which should not be re-labeled
)
// Perform the 1D split operation
// This writes new labels back to the original vector, while returning a new incidence matrix
{
	const int block_index = index - block_start;
	const int block_size = block_end - block_start;
	py_assert(block_size > 0, "Block is empty");
	py_assert(0 <= block_index && block_index < block_labels.shape(0), "Index out of bounds");
	int64_t* block_labels_data = static_cast<int64_t*>(block_labels.request().ptr);
	// Find the connected component of the label to split
	std::unordered_set<int64_t> cc = find_connected_component(label, linkage);
	// Find next available label, if it exists
	std::optional<int64_t> next_label = find_next_label(block_labels, 0, block_size, block_start, block_end);
	// If the next label is available, do the relabeling (otherwise we're done)
	LabelMap label_map;
	if (next_label) {
		const int64_t nlb = *next_label;
		// Relabel the connected component to the right of the split index, respecting preserved_indices
		const int N = block_labels.shape(0);
		for (int i=block_index; i<N; i++) {
			const int64_t lb = block_labels_data[i];
			if (cc.count(lb) && !preserved_indices.count(i+block_start)) {
				label_map[lb] = nlb;
				block_labels_data[i] = nlb;
			}
		}
		// Unlink the new label from the graph
		unlink_nodes({nlb}, linkage);
	}
	// Update the incidence matrix
	bool* li_data = static_cast<bool*>(std::get<0>(linkage).request().ptr);
	int64_t* li_indices = static_cast<int64_t*>(std::get<1>(linkage).request().ptr);
	int64_t* li_indptr = static_cast<int64_t*>(std::get<2>(linkage).request().ptr);
	const int nrows = std::get<0>(std::get<3>(linkage));
	for (int i=0; i<nrows; i++) {
		if (li_indptr[i] + 2 == li_indptr[i+1]) { // There appears to be an edge
			int j_u = li_indptr[i];
			int j_v = j_u + 1;
			if (li_data[j_u] && li_data[j_v]) { // The edge is real
				int64_t u = li_indices[j_u];
				int64_t v = li_indices[j_v];
				if (cc.count(u) && cc.count(v)) { // The edge is in the connected component
					if (v < u) { // WLOG, u <= v
						std::swap(u, v);
						std::swap(j_u, j_v);
					}
					if (u < index && v >= index) { // The split operation intersects the edge
						if (next_label) { // If there is a new label u', translate u -> u'
							li_indices[j_u] = *next_label;
						} else { // Otherwise, delete the edge
							li_data[j_u] = false;
							li_data[j_v] = false;
						}
					}
				}
			}
		}
	}
	return label_map;
}

LabelMap split_blocks_2d(
	py::array_t<int64_t> labels, 							// Labels in the blocks being split (written to)
	const int blocks_start, 									// Start index of the blocks
	const int blocks_end, 										// End index of the blocks
	const int block_size, 										// Size of the block
	const std::unordered_set<int>& indices, 	// Labels to exclude from the split
	const int64_t label, 											// Label to split
	EVIncidence linkage												// Linkage matrix (written to)
)
// Re-label units in a region according to an inclusion or exclusion criterion,
// and return any newly created labels. Does not add the necessary links to associated said labels.
{
	const int N = labels.shape(0);
	const int n_blocks = (blocks_end - blocks_start) / block_size;
	py_assert(n_blocks > 0, "No blocks to split");
	py_assert(n_blocks * block_size >= N, "Number of labels does not match number of blocks");
	int64_t* labels_data = static_cast<int64_t*>(labels.request().ptr);
	// Find the connected component of the label to split
	std::unordered_set<int64_t> cc = find_connected_component(label, linkage);
	// Newly created labels
	std::unordered_set<int64_t> new_labels;
	LabelMap label_map; // Map from old labels to new labels
	std::unordered_map<int64_t, std::optional<int64_t>> cache_label_map; // Secondary label map to avoid re-computing new labels
	// Relabel the data according to the inclusion/exclusion rule
	for (int i=0; i<n_blocks; i++) {
		const int j1 = i * block_size;
		const int j2 = std::min(N, (i+1) * block_size);
		const int block_start = blocks_start + j1;
		const int block_end = blocks_start + j2;
		for (int j=j1; j<j2; j++) {
			int64_t lb = labels_data[j];
			int lb_index = j + blocks_start;
			if (
				cc.count(lb) && // In the connected component
				indices.count(lb_index) // In the set that needs relabeling
			) {
				if (cache_label_map.find(lb) == cache_label_map.end()) {
					// If the label is not in the lookup map, generate a new one
					auto new_lb = find_next_label(labels, j1, j2, block_start, block_end);
					cache_label_map[lb] = new_lb;
					if (new_lb) {
						new_labels.insert(*new_lb);
						label_map[lb] = *new_lb;
						labels_data[j] = *new_lb;
					} else {
						std::cout << "Requested new label for: " << lb << " but found none" << std::endl;
					}
				} else {
					// Else, use the existing one
					auto new_lb = cache_label_map[lb];
					if (new_lb) {
						labels_data[j] = *new_lb;
					}
				}
			}
		}
	}
	// Unlink the new labels from the graph
	unlink_nodes(new_labels, linkage);
	return label_map;
}

std::optional<int64_t> find_next_label(
	py::array_t<int64_t> labels,  // Labels within which to search
	const int index_start,				// Start index within the labels array
	const int index_end,					// End index within the labels array
	const int block_start,				// Start index of the block
	const int block_end						// End index of the block
)
// Find next available label in the block
{
	int64_t* labels_data = static_cast<int64_t*>(labels.request().ptr);
	std::unordered_set<int64_t> used;
	for (int i=index_start; i<index_end; i++) {
		used.insert(labels_data[i]);
	}
	for (int64_t lb = block_start; lb < block_end; lb++) {
		if (used.find(lb) == used.end()) {
			return { lb };
		}
	}
	return std::nullopt;
}

void relabel(
	py::array_t<int64_t> labels, 													// Labels (written to)
	const std::unordered_map<int64_t, int64_t>& label_map // Map from old labels to new labels
)
// Apply a relabeling
{
	int64_t* labels_data = static_cast<int64_t*>(labels.request().ptr);
	for (int i=0; i<labels.shape(0); i++) {
		if (label_map.count(labels_data[i])) {
			labels_data[i] = label_map.at(labels_data[i]);
		}
	}
}