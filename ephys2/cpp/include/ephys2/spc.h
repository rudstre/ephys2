#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

// Include C sources
extern "C" {
	#include "../spc/SW.h"
}

#ifndef SPC_H
#define SPC_H

namespace py = pybind11;

using SPCResult = std::tuple<
	py::array_t<float>,					// Temperatures
	py::array_t<unsigned int> 	// Cluster assignments in row-major order (K temps x N samples)
>;

SPCResult super_paramagnetic_clustering(
	py::array_t<double> dists, 	// Matrix of pairwise distances between samples (N_samples, N_samples)
	const float Tmin, 					// Minimum temperature
	const float Tmax, 					// Maximum temperature
	const float Tstep, 					// Temperature step
	const size_t cyc,						// Total number of cycles
	const int K, 								// Maximal number of nearest neighbours (used in the knn algorithm)
	const bool MSTree, 					// Whether to add the edges of the minimal spanning tree (should default to True)
	const std::optional<int> seed		// Random seed
	);

UIRaggedArray knn(const size_t N, const size_t K, const bool MSTree, py::array_t<double> dists );

void mstree(const size_t N, py::array_t<double> dists, unsigned int** edg);

EdgeDistanceResult EdgeDistance( UIRaggedArray NK, py::array_t<double> dists );

#endif