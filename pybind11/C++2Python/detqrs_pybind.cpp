#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "detqrs_deriv_brev.h"

namespace py = pybind11;

PYBIND11_MODULE(detqrs, m)
{
    m.doc() =
        "Binding Python do detector de QRS por derivacao e busca reversa";

    py::class_<DetQRS>(m, "DetQRS")
        .def(py::init<int, int>())
        .def("Inicia",[](DetQRS &self,
            py::array_t<float,py::array::c_style | py::array::forcecast> sinal)
            {
                py::buffer_info buf = sinal.request();
                self.Inicia(static_cast<float *>(buf.ptr),static_cast<int>(buf.size));
            }
        )
        .def("RetDimBlocoAmostras",&DetQRS::RetDimBlocoAmostras)
        .def("Processa",[](DetQRS &self,
            py::array_t<float,py::array::c_style | py::array::forcecast> sinal)
            {
                py::buffer_info buf = sinal.request();
                std::unique_ptr<int[]> qrs(new int[static_cast<std::size_t>(buf.size)]);

                const int n_qrs = self.Processa(
                    static_cast<float *>(buf.ptr),
                    qrs.get()
                );

                const int n_saida = (n_qrs < 0) ? -n_qrs : n_qrs;

                py::array_t<int> saida(n_saida);
                auto out = saida.mutable_unchecked<1>();

                for (int i = 0; i < n_saida; ++i)
                    out(i) = qrs[i];

                return py::make_tuple(n_qrs, saida);
            }
        );
}
