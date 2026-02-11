#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>

namespace py = pybind11;

double los_boolean(
    py::array_t<float, py::array::c_style | py::array::forcecast> heightmap,
    int width,
    int height,
    double x0, double y0, double z0,
    double x1, double y1, double z1
) {
    auto buf = heightmap.request();
    float* ptr = static_cast<float*>(buf.ptr);

    // Direction
    double dx = x1 - x0;
    double dy = y1 - y0;
    double dz = z1 - z0;

    // Current grid cell
    int x = static_cast<int>(std::floor(x0));
    int y = static_cast<int>(std::floor(y0));

    int endX = static_cast<int>(std::floor(x1));
    int endY = static_cast<int>(std::floor(y1));

    int stepX = (dx > 0) ? 1 : -1;
    int stepY = (dy > 0) ? 1 : -1;

    double tMaxX, tMaxY;
    double tDeltaX, tDeltaY;

    if (dx != 0) {
        double nextGridX = (stepX > 0) ? (x + 1.0) : x;
        tMaxX = (nextGridX - x0) / dx;
        tDeltaX = 1.0 / std::abs(dx);
    } else {
        tMaxX = std::numeric_limits<double>::infinity();
        tDeltaX = tMaxX;
    }

    if (dy != 0) {
        double nextGridY = (stepY > 0) ? (y + 1.0) : y;
        tMaxY = (nextGridY - y0) / dy;
        tDeltaY = 1.0 / std::abs(dy);
    } else {
        tMaxY = std::numeric_limits<double>::infinity();
        tDeltaY = tMaxY;
    }

    while (true) {

        if (x < 0 || y < 0 || x >= width || y >= height)
            return 0.0;

        // Compute parametric t along ray
        double t;

        if (std::abs(dx) > std::abs(dy))
            t = (x - x0) / dx;
        else
            t = (y - y0) / dy;

        if (t < 0) t = 0;
        if (t > 1) t = 1;

        double rayHeight = z0 + t * dz;

        float terrain = ptr[y * width + x];

        if (terrain > rayHeight)
            return 0.0;

        if (x == endX && y == endY)
            break;

        if (tMaxX < tMaxY) {
            tMaxX += tDeltaX;
            x += stepX;
        } else {
            tMaxY += tDeltaY;
            y += stepY;
        }
    }

    return 1.0;
}

PYBIND11_MODULE(los, m) {
    m.def("los_boolean", &los_boolean);
}