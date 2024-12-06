#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <stdexcept>

#ifndef UTILS_H
#define UTILS_H

namespace py = pybind11;

// NOTE: The following wrapper methods give memory ownership of containers created in C++ to NumPy.
// This ensures correct GC/deallocation semantics in Python.
//
// See:
// https://stackoverflow.com/questions/44659924/returning-numpy-arrays-via-pybind11
// https://github.com/pybind/pybind11/issues/1042
// https://github.com/ssciwr/pybind11-numpy-example

template <typename Sequence>
inline py::array_t<typename Sequence::value_type> seq2numpy(Sequence &seq, std::vector<size_t> shape) 
// Zero-copy numpy conversion for C++ containers
{
  auto data = seq.data();
  std::unique_ptr<Sequence> seq_ptr = std::make_unique<Sequence>(std::move(seq));
  auto capsule = py::capsule(seq_ptr.get(), [](void *p) { 
  	std::unique_ptr<Sequence>(reinterpret_cast<Sequence*>(p));
  });
  seq_ptr.release();
  return py::array(shape, data, capsule);
}

template <typename T>
inline py::array_t<T> arr2numpy(T *data, std::vector<size_t> shape)
// Zero-copy numpy conversion for C-style arrays
{
	// TODO: should we use std::unique_ptr approach as above?
	auto capsule = py::capsule(data, [](void *d) {
		T *data = reinterpret_cast<T *>(d);
		// std::cerr << "Element [0] = " << data[0] << "\n";
	 // 	std::cerr << "freeing memory @ " << d << "\n";
		delete[] data;
	});
	return py::array_t<T>(shape, data, capsule);
}

std::vector<size_t> calc_strides(size_t *shape, size_t size, size_t ndim);

inline void py_assert(bool cond, const std::string& msg)
// Python-friendly assertion
{
	if (! cond) {
		throw std::runtime_error(msg);
	}
}

#endif