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

double los_probability(
    py::array_t<float, py::array::c_style | py::array::forcecast> heightmap,
    int width,
    int height,
    double x0, double y0, double z0,
    double x1, double y1, double z1,
    int num_samples = 9
) {
    // Sample multiple rays in a pattern around the primary ray
    // Returns probability as fraction of successful rays
    
    if (num_samples == 1) {
        return los_boolean(heightmap, width, height, x0, y0, z0, x1, y1, z1);
    }
    
    int successful_rays = 0;
    
    // Sample in a grid pattern around the endpoints
    // For 9 samples: center + 8 surrounding points
    // For 25 samples: 5x5 grid, etc.
    
    int grid_size = static_cast<int>(std::sqrt(num_samples));
    if (grid_size * grid_size < num_samples) grid_size++;
    
    double offset_range = 2.0; // Sample within +/- 2 grid cells
    
    for (int i = 0; i < num_samples; i++) {
        // Calculate offset pattern
        int grid_x = i % grid_size;
        int grid_y = i / grid_size;
        
        double offset_x = (grid_x - grid_size / 2.0) * (offset_range / grid_size);
        double offset_y = (grid_y - grid_size / 2.0) * (offset_range / grid_size);
        
        // Apply offset to both endpoints
        double sample_x0 = x0 + offset_x;
        double sample_y0 = y0 + offset_y;
        double sample_x1 = x1 + offset_x;
        double sample_y1 = y1 + offset_y;
        
        // Check LOS for this sample
        double result = los_boolean(heightmap, width, height,
                                   sample_x0, sample_y0, z0,
                                   sample_x1, sample_y1, z1);
        
        if (result > 0.5) {
            successful_rays++;
        }
    }
    
    return static_cast<double>(successful_rays) / num_samples;
}

PYBIND11_MODULE(los, m) {
    m.def("los_boolean", &los_boolean, 
          py::arg("heightmap"),
          py::arg("width"),
          py::arg("height"),
          py::arg("x0"), py::arg("y0"), py::arg("z0"),
          py::arg("x1"), py::arg("y1"), py::arg("z1"),
          "Check line-of-sight between two points (returns 0.0 or 1.0)");
    
    m.def("los_probability", &los_probability,
          py::arg("heightmap"),
          py::arg("width"),
          py::arg("height"),
          py::arg("x0"), py::arg("y0"), py::arg("z0"),
          py::arg("x1"), py::arg("y1"), py::arg("z1"),
          py::arg("num_samples") = 9,
          "Compute line-of-sight probability by sampling multiple rays (returns 0.0 to 1.0)");
}