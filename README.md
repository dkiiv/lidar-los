# lidar-los
Line-Of-Sight for 2 points in point cloud

## Prereqs
> conda

## Setup Environment
```bash
conda create -y -n los-env python=3.11
conda activate los-env
conda install -y -c conda-forge pybind11 cmake ninja compilers rasterio pdal requests laspy scipy
```

## General Pipeline
> USGS LAZ (LiDAR)  →  DEM raster (preprocessing)  →  processor, currently classical eventually ML

## Workflow

### 1. Download USGS LiDAR Data
Use the provided script to download LAZ files from USGS based on GPS coordinates:

```bash
# Download real USGS data (if available for location)
python fetch_usgs_lidar.py --lat 39.7392 --lon -104.9903

# Or create sample data for testing
python fetch_usgs_lidar.py --lat 39.7392 --lon -104.9903 --sample

# Specify output directory
python fetch_usgs_lidar.py --lat 36.1069 --lon -112.1129 --output-dir ./data --sample
```

**Example Coordinates:**
- Denver, CO: `--lat 39.7392 --lon -104.9903`
- Grand Canyon: `--lat 36.1069 --lon -112.1129`
- Mount Rainier: `--lat 46.8523 --lon -121.7603`
- San Francisco: `--lat 37.7749 --lon -122.4194`

### 2. Convert LAZ to DEM Raster
The fetch script automatically converts LAZ files to GeoTIFF DEM rasters using PDAL/rasterio.

Output files in `lidar_data/` directory:
- `*.laz` - Compressed LiDAR point cloud
- `*_dem.tif` - DEM raster (GeoTIFF format)
- `*_dem.npy` - DEM as numpy array (for direct use)

### 3. Build C++ Extension
```bash
python setup.py build_ext --inplace
```

**Rebuild C++ Extension:**
```bash
rm -rf build
rm los*.so
python setup.py build_ext --inplace
```

### 4. Run Line-of-Sight Analysis

**With downloaded/sample data:**
```python
python usgs_los_test.py
```

**Manual usage:**
```python
import numpy as np
import los

# Load DEM
dem = np.load('lidar_data/sample_lidar_39.7392_-104.9903_dem.npy')

# Check line of sight between two points
result = los.los_boolean(
    dem,
    dem.shape[1],  # width
    dem.shape[0],  # height
    x0, y0, z0,    # observer position
    x1, y1, z1     # target position
)

# Or get probability
probability = los.los_probability(
    dem,
    dem.shape[1],
    dem.shape[0],
    x0, y0, z0,
    x1, y1, z1
)
```

## Testing

**Static test (synthetic data):**
```python
python static_test.py
```

**USGS data test:**
```python
python usgs_los_test.py
```

## USGS Data Notes

- USGS LiDAR coverage varies by location
- Script will attempt to find real data first
- Falls back to sample generation if no data available
- Check coverage: https://apps.nationalmap.gov/downloader/

## File Formats

**Input:** LAZ (LASer Zip) - compressed LiDAR point cloud  
**Intermediate:** GeoTIFF DEM raster  
**Runtime:** NumPy array (float32)

## Troubleshooting

**Missing PDAL:**
```bash
conda install -c conda-forge pdal python-pdal
```

**LAZ file errors:**
```bash
conda install -c conda-forge lazperf
```

**No data for location:**
- Use `--sample` flag to generate test data
- Try different coordinates
- Check USGS coverage maps