#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>

namespace py = pybind11;

double los_probability(
    py::array_t<float, py::array::c_style | py::array::forcecast> heightmap,
    int width,
    int height,
    double x0, double y0, double z0,
    double x1, double y1, double z1
) {
    auto buf = heightmap.request();
    float* ptr = static_cast<float*>(buf.ptr);

    int steps = 500;

    for (int i = 0; i < steps; i++) {
        double t = static_cast<double>(i) / steps;

        double x = x0 + t * (x1 - x0);
        double y = y0 + t * (y1 - y0);
        double z = z0 + t * (z1 - z0);

        int xi = static_cast<int>(x);
        int yi = static_cast<int>(y);

        if (xi < 0 || yi < 0 || xi >= width || yi >= height)
            return 0.0;

        float terrain = ptr[yi * width + xi];

        if (terrain > z)
            return 0.0;
    }

    return 1.0;
}

PYBIND11_MODULE(los, m) {
    m.def("los_probability", &los_probability);
}