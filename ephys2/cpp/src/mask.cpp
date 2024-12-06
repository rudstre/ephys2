#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <string>

#include "../include/ephys2/utils.h"
#include "../include/ephys2/mask.h"

namespace py = pybind11;

void apply_venn_mask(
	Venn& venn,										// Venn diagram (list of sets and boolean values)
	py::array_t<int64_t> labels,	// Labels to apply the mask to
	py::array_t<bool> mask 				// Mask to update
)
// Apply a Venn diagram to a set of labels to construct a mask
{
	py_assert(labels.shape(0) == mask.shape(0), "Labels and mask must have the same length");
	const int N = labels.shape(0);
	int64_t* labels_data = static_cast<int64_t*>(labels.request().ptr);
	bool* mask_data = static_cast<bool*>(mask.request().ptr);
	for (int i=0; i<N; i++) {
		int64_t label = labels_data[i];
		bool value = true;
		for (auto& v : venn) {
			if ((std::get<0>(v).find(label) == std::get<0>(v).end()) != std::get<1>(v)) {
				// If the inclusion test matches the inclusion condition, set the mask false
				value = false;
				break;
			}
		}
		mask_data[i] = value;
	}
}