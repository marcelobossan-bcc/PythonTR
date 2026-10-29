c++ -O3 -Wall -shared -std=c++17 -fPIC $(python3 -m pybind11 --includes) detqrs_pybind.cpp detqrs_deriv_brev.cpp filtro.cpp  -o detqrs$(python3-config --extension-suffix)
