# lidar-los
LOS for 2 points in point cloud

## Prereqs
Python;
`pip install pybind11`

`pip install pdal`

## General order
> USGS LAZ (LiDAR)  →  DEM raster (preprocessing)  →  processor, currently classical eventually ML

### Build it -- classical
``python setup.py build_ext --inplace``

Import `los.cpython-XXX.so` into python runtime
```
import los

p = los.los_probability(
    dem_array,
    width,
    height,
    x0, y0, z0,
    x1, y1, z1
)
```