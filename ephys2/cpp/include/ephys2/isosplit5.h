/*
 * Copyright 2016-2017 Flatiron Institute, Simons Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * 
 * Modified 3/7/22 Anand Srinivasan.
 */

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#ifndef ISOSPLIT5_H
#define ISOSPLIT5_H

//#include "mlcommon.h"
#include "../isosplit5/isocut5.h"

namespace py = pybind11;

struct isosplit5_opts {
	float isocut_threshold = 1.0;
	int min_cluster_size = 10;
	int K_init = 200;
	bool refine_clusters = false;
	int max_iterations_per_pass = 500;
};

bool isosplit5(
	py::array_t<float> X,
	py::array_t<int> y, 
	const std::optional<float> isocut_threshold,
	const std::optional<int> min_cluster_size,
	const std::optional<int> K_init,
	const std::optional<bool> refine_clusters,
	const std::optional<int> max_iterations_per_pass,
  const std::optional<int> seed       
	);

bool isosplit5_rec(
	int* labels_out, 
	bigint M, 
	bigint N, 
	float* X, 
	isosplit5_opts opts
	);

#endif 
