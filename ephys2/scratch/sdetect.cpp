// Modification of torchaudio::lfilter

#include <torch/script.h>
#include <torch/torch.h>
#include <torch/extension.h>

using namespace torch::indexing;

torch::Tensor sdetect(
    torch::Tensor signals,
    torch::Tensor signal_groups,
    double threshold) {

}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("sdetect", &sdetect, "sdetect");
}