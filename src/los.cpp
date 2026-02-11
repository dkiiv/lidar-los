#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>

namespace py = pybind11;

double los_probability(
    py::array_t<double> heightmap,
    int width,
    int height,
    double x0, double y0, double z0,
    double x1, double y1, double z1
) {
    auto buf = heightmap.request();
    double* ptr = (double*) buf.ptr;

    int steps = 500;
    for (int i = 0; i < steps; i++) {
        double t = (double)i / steps;

        double x = x0 + t * (x1 - x0);
        double y = y0 + t * (y1 - y0);
        double z = z0 + t * (z1 - z0);

        int xi = (int)x;
        int yi = (int)y;

        if (xi < 0 || yi < 0 || xi >= width || yi >= height)
            return 0.0;

        double terrain = ptr[yi * width + xi];

        if (terrain > z)
            return 0.0;
    }

    return 1.0;
}

PYBIND11_MODULE(los, m) {
    m.def("los_probability", &los_probability);
}