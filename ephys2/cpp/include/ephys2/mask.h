#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#ifndef MASK_H
#define MASK_H

namespace py = pybind11;

using Venn = std::vector<std::tuple<std::unordered_set<int64_t>, bool>>;

void apply_venn_mask(
	Venn& venn,										// Venn diagram (list of sets and boolean values)
	py::array_t<int64_t> labels,	// Labels to apply the mask to
	py::array_t<bool> mask 				// Mask to update
);

#endif
