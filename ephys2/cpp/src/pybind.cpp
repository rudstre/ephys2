#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "../include/ephys2/rhd2000.h"
#include "../include/ephys2/rhd64.h"
#include "../include/ephys2/intan_ofps.h"
#include "../include/ephys2/snippet.h"
#include "../include/ephys2/detect.h"
// #include "../include/ephys2/sosfilt.h"
#include "../include/ephys2/spc.h"
#include "../include/ephys2/isosplit5.h"
#include "../include/ephys2/align.h"
#include "../include/ephys2/link.h"
#include "../include/ephys2/split.h"
#include "../include/ephys2/mask.h"

namespace py = pybind11;

PYBIND11_MODULE(_cpp, m) {

	m.doc() = R"pbdoc(
			Pybind11 example plugin
			-----------------------
			.. currentmodule:: scikit_build_example
			.. autosummary::
				 :toctree: _generate
				 add
				 subtract
	)pbdoc";

	// Bind selected functions to Python module

	m.def("snippet_channel_groups", &snippet_channel_groups, R"pbdoc(
			Add two numbers
			Some other explanation about the add function.
	)pbdoc", 
		py::arg().noconvert(),
		py::arg().noconvert(),
		py::arg(),
		py::arg(),
		py::arg(),
		py::arg(),
		py::arg()
	);

	m.def("detect_channel", &detect_channel, R"pbdoc(
			Add two numbers
			Some other explanation about the add function.
	)pbdoc", 
		py::arg().noconvert(),
		py::arg().noconvert(),
		py::arg(),
		py::arg()
	);

	m.def("read_rhd2000_batch", &read_rhd2000_batch, R"pbdoc(
			Add two numbers
			Some other explanation about the add function.
	)pbdoc");

	m.def("read_rhd64_batch", &read_rhd64_batch, R"pbdoc(
			Add two numbers
			Some other explanation about the add function.
	)pbdoc");

	m.def("read_intan_ofps_batch", &read_intan_ofps_batch, R"pbdoc(
			Add two numbers
			Some other explanation about the add function.
	)pbdoc");

	// m.def("sosfiltfilt2d", &sosfiltfilt2d, R"pbdoc(
	//     Add two numbers
	//     Some other explanation about the add function.
	// )pbdoc",
	// 	py::arg().noconvert(),
	// 	py::arg().noconvert(),
	// 	py::arg().noconvert(),
	// 	py::arg(),
	// 	py::arg()
	// );

	m.def("super_paramagnetic_clustering", &super_paramagnetic_clustering, R"pbdoc(
			Add two numbers
			Some other explanation about the add function.
	)pbdoc",
		py::arg().noconvert(),
		py::arg(),
		py::arg(),
		py::arg(),
		py::arg(),
		py::arg(),
		py::arg(),
		py::arg()
	);

	m.def("isosplit5", &isosplit5, "ISO-SPLIT clustering",
		py::arg("X").noconvert(),
		py::arg("y").noconvert(),
		py::arg("isocut_threshold"),
		py::arg("min_cluster_size"),
		py::arg("K_init"),
		py::arg("refine_clusters"),
		py::arg("max_iterations_per_pass"),
		py::arg("seed")
	);

	m.def("align_sequences", &align_sequences, "Align sequences",
		py::arg("times1").noconvert(),
		py::arg("times2").noconvert(),
		py::arg("vals1").noconvert(),
		py::arg("vals2").noconvert(),
		py::arg("max_dist"),
		py::arg("fill_value")
	);

	m.def("link_labels", &link_labels, "Link labels",
		py::arg("unlinked").noconvert(),
		py::arg("linked").noconvert(),
		py::arg("linkage").noconvert()
	);

	m.def("relabel_by_cc", &relabel_by_cc, "Relabel by connected component",
		py::arg("label"),
		py::arg("linkage").noconvert()
	);

	m.def("split_block_1d", &split_block_1d, "Split block 1d",
		py::arg("block_labels").noconvert(),
		py::arg("block_start"),
		py::arg("block_end"),
		py::arg("index"),
		py::arg("label"),
		py::arg("linkage").noconvert(),
		py::arg("preserved_indices").noconvert()
	);

	m.def("split_blocks_2d", &split_blocks_2d, "Split blocks 2d",
		py::arg("labels").noconvert(),
		py::arg("blocks_start"),
		py::arg("blocks_end"),
		py::arg("block_size"),
		py::arg("indices").noconvert(),
		py::arg("label"),
		py::arg("linkage").noconvert()
	);

	m.def("relabel", &relabel, "Relabel",
		py::arg("labels").noconvert(),
		py::arg("label_map").noconvert()
	);

	m.def("find_connected_component", &find_connected_component, "Find connected component",
		py::arg("label"),
		py::arg("linkage").noconvert()
	);

	m.def("filter_by_cc", &filter_by_cc, "Filter by connected component",
		py::arg("node"),
		py::arg("linkage").noconvert(),
		py::arg("labels").noconvert(),
		py::arg("array").noconvert()
	);

	m.def("apply_venn_mask", &apply_venn_mask, "Apply venn mask",
		py::arg("venn").noconvert(),
		py::arg("labels").noconvert(),
		py::arg("mask").noconvert()
	);
}