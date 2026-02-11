# lidar-los
LOS for 2 points in point cloud

## Prereqs
> conda


## General order
> USGS LAZ (LiDAR)  →  DEM raster (preprocessing)  →  processor, currently classical eventually ML

### Build it -- classical
```
conda create -y -n los-env python=3.11
conda activate los-env
conda install -y -c conda-forge pybind11 cmake ninja compilers rasterio pdal
```

``python src/setup.py build_ext --inplace``

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