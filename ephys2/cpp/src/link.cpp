#include <iostream>
#include <string>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <queue>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/link.h"

namespace py = pybind11;

void link_labels(
	py::array_t<int64_t> unlinked, 	// Un-linked labels
	py::array_t<int64_t> linked, 		// Linked labels (written to)
	EVIncidence linkage 						// Linkage matrix
)
// Link labels using an edge-vertex incidence matrix, returning the minimum label for each connected component
{
	py_assert(unlinked.shape(0) == linked.shape(0), "Input arrays must have the same shape");
	std::unordered_map<int64_t, int64_t> label_map;
	int64_t* unlinked_data = static_cast<int64_t*>(unlinked.request().ptr);
	int64_t* linked_data = static_cast<int64_t*>(linked.request().ptr);

	const int N = unlinked.shape(0);
	for (int i = 0; i < N; i++) {
		int64_t label = unlinked_data[i];
		if (label_map.find(label) == label_map.end()) {
			// Label not found; compute and store connected component 
			std::unordered_set<int64_t> cc = find_connected_component(label, linkage);
			int64_t min_label = *std::min_element(cc.begin(), cc.end());
			for (int64_t v : cc) {
				label_map[v] = min_label;
			}
			linked_data[i] = min_label;
		} else {
			linked_data[i] = label_map[label];
		}
	}
}

int64_t relabel_by_cc(
	int64_t label, 							// Label to relabel
	EVIncidence linkage 				// Linkage matrix
) {
	// Find connected component of label
	std::unordered_set<int64_t> cc = find_connected_component(label, linkage);
	// Return minimum label
	return *std::min_element(cc.begin(), cc.end());
}

std::unordered_set<int64_t> find_connected_component(
	int64_t node,											// Node
	EVIncidence linkage								// Linkage matrix
)
// Find the connected component for a given node using BFS
{
	bool* data = static_cast<bool*>(std::get<0>(linkage).request().ptr);
	int64_t* indices = static_cast<int64_t*>(std::get<1>(linkage).request().ptr);
	int64_t* indptr = static_cast<int64_t*>(std::get<2>(linkage).request().ptr);
	const int nrows = std::get<0>(std::get<3>(linkage));
	
	std::unordered_set<int64_t> seen;
	std::queue<int64_t> queue;
	queue.push(node);
	while (!queue.empty()) {
		int64_t v = queue.front();
		queue.pop();
		if (seen.find(v) == seen.end()) {
			// Node not seen yet; add to connected component
			seen.insert(v);
			// Find neighbors from CSR edge-vertex incidence matrix
			for (int j = 0; j < nrows; j++) {
				bool edge_exists = false;
				for (int k = indptr[j]; k < indptr[j+1]; k++) {
					if (indices[k] == v && data[k]) {
						// Edge involving current node exists
						edge_exists = true;
					}
				}
				if (edge_exists) {
					// Add neighbors to queue
					for (int k = indptr[j]; k < indptr[j+1]; k++) {
						if (indices[k] != v && data[k]) {
							queue.push(indices[k]);
						}
					}
				}
			}
		}
	}
	return seen;
}

py::array_t<int64_t> filter_by_cc(
	int64_t node, 									// Node
	EVIncidence linkage,						// Linkage matrix
	py::array_t<int64_t> labels,		// Labels
	py::array_t<int64_t> array			// Array to filter (should be same shape as labels)
)
// Filter an array by the elements whose labels are within a connected component
{
	py_assert(labels.shape(0) == array.shape(0), "Input arrays must have the same shape");
	const int N = labels.shape(0);
	std::unordered_set<int64_t> cc = find_connected_component(node, linkage);
	int64_t* labels_data = static_cast<int64_t*>(labels.request().ptr);
	int64_t* array_data = static_cast<int64_t*>(array.request().ptr);
	std::vector<int64_t> filtered;
	for (int i = 0; i < N; i++) {
		if (cc.find(labels_data[i]) != cc.end()) {
			filtered.push_back(array_data[i]);
		}
	}
	return seq2numpy(filtered, {filtered.size()});
}

void unlink_nodes(
	const std::unordered_set<int64_t>& nodes, 	// Nodes 
	EVIncidence linkage 												// Linkage matrix
)
// Disconnect all edges to a set of nodes
{
	bool* data = static_cast<bool*>(std::get<0>(linkage).request().ptr);
	int64_t* indices = static_cast<int64_t*>(std::get<1>(linkage).request().ptr);
	int64_t* indptr = static_cast<int64_t*>(std::get<2>(linkage).request().ptr);
	const int nrows = std::get<0>(std::get<3>(linkage));
	
	for (int j = 0; j < nrows; j++) {
		bool needs_unlinking = false;
		for (int k = indptr[j]; k < indptr[j+1]; k++) {
			if (nodes.count(indices[k]) && data[k]) {
				needs_unlinking = true;
			}
		}
		if (needs_unlinking) {
			// Remove edge
			for (int k = indptr[j]; k < indptr[j+1]; k++) {
				data[k] = false;
			}
		}
	}
}