#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef LINK_H
#define LINK_H

namespace py = pybind11;

using EVIncidence = std::tuple<
	py::array_t<bool>, 									// Data
	py::array_t<int64_t>, 							// Indices
	py::array_t<int64_t>, 							// Indptr
	std::tuple<int, int> 								// Shape
>;

void link_labels(
	py::array_t<int64_t> unlinked, 	// Un-linked labels
	py::array_t<int64_t> linked, 		// Linked labels (written to)
	EVIncidence linkage 						// Linkage matrix
);

int64_t relabel_by_cc(
	int64_t label, 							// Label to relabel
	EVIncidence linkage 				// Linkage matrix
);

std::unordered_set<int64_t> find_connected_component(
	int64_t node,											// Node
	EVIncidence linkage								// Linkage matrix
);

py::array_t<int64_t> filter_by_cc(
	int64_t node, 									// Node
	EVIncidence linkage,						// Linkage matrix
	py::array_t<int64_t> labels,		// Labels
	py::array_t<int64_t> array			// Array to filter (should be same shape as labels)
);

void unlink_nodes(
	const std::unordered_set<int64_t>& nodes, 	// Nodes 
	EVIncidence linkage 												// Linkage matrix
);

#endif
