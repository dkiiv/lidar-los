#!/usr/bin/env python3
"""
USGS LiDAR Data Fetcher and DEM Converter
Downloads LAZ files from USGS 3DEP and converts them to DEM rasters for los.cpp

Usage:
    python fetch_usgs_lidar.py --lat 39.7392 --lon -104.9903 --sample
"""

import argparse
import requests
import json
import os
import sys
from pathlib import Path

try:
    import laspy
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    from scipy.interpolate import griddata
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with conda:")
    print("  conda install -c conda-forge laspy rasterio scipy")
    sys.exit(1)


class USGSLidarFetcher:
    """Fetches and processes USGS 3DEP LiDAR data into DEM rasters"""
    
    def __init__(self, lat, lon, output_dir="lidar_data", resolution=1.0):
        self.lat = lat
        self.lon = lon
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.resolution = resolution  # meters per pixel
        
    def find_lidar_tiles(self):
        """
        Query USGS The National Map API to find available LiDAR tiles
        """
        print(f"Searching for LiDAR data at ({self.lat}, {self.lon})...")
        
        # The National Map API endpoint
        base_url = "https://tnmaccess.nationalmap.gov/api/v1/products"
        
        # Calculate bounding box (roughly 0.01 degrees ~ 1km)
        bbox_size = 0.01
        bbox = f"{self.lon - bbox_size},{self.lat - bbox_size},{self.lon + bbox_size},{self.lat + bbox_size}"
        
        params = {
            "datasets": "Lidar Point Cloud (LPC)",
            "bbox": bbox,
            "outputFormat": "JSON",
            "max": 10
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('total', 0) == 0:
                print("No LiDAR data found for this location.")
                return []
            
            items = data.get('items', [])
            print(f"Found {len(items)} LiDAR datasets")
            
            return items
            
        except Exception as e:
            print(f"Error querying USGS API: {e}")
            return []
    
    def download_laz_file(self, download_url, filename=None):
        """
        Download a LAZ file from the given URL
        """
        if filename is None:
            filename = f"lidar_{self.lat}_{self.lon}.laz"
        
        output_path = self.output_dir / filename
        
        print(f"Downloading {filename}...")
        print(f"URL: {download_url}")
        
        try:
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                if total_size > 0:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end='', flush=True)
                    print()
                else:
                    f.write(response.content)
            
            print(f"Downloaded to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def create_sample_laz(self):
        """
        Create a sample LAZ file for testing purposes
        This simulates terrain around the given coordinates
        """
        print("Creating sample LiDAR data for testing...")
        
        # Generate synthetic terrain data
        n_points = 100000
        
        # Create a grid of points with elevation variation
        x = np.random.uniform(-50, 50, n_points)
        y = np.random.uniform(-50, 50, n_points)
        
        # Simulate terrain with some hills and valleys
        z = (
            10 * np.sin(x / 10) * np.cos(y / 10) +  # Rolling hills
            5 * np.sin(x / 5) +  # Larger features
            3 * np.cos(y / 8) +  # Cross valleys
            np.random.normal(0, 0.5, n_points)  # Noise
        )
        
        # Add some peaks
        for peak_x, peak_y, peak_h in [(20, 20, 30), (-25, -15, 25)]:
            dist = np.sqrt((x - peak_x)**2 + (y - peak_y)**2)
            z += peak_h * np.exp(-dist / 10)
        
        # Create LAS file
        header = laspy.LasHeader(point_format=3, version="1.2")
        header.offsets = [0, 0, 0]
        header.scales = [0.01, 0.01, 0.01]
        
        las = laspy.LasData(header)
        
        las.x = x
        las.y = y
        las.z = z
        
        # Add intensity values
        las.intensity = np.random.randint(0, 65535, n_points, dtype=np.uint16)
        
        output_path = self.output_dir / f"sample_lidar_{self.lat}_{self.lon}.laz"
        las.write(str(output_path))
        
        print(f"Created sample LAZ file: {output_path}")
        print(f"  Points: {n_points}")
        print(f"  Bounds: X[{x.min():.1f}, {x.max():.1f}] "
              f"Y[{y.min():.1f}, {y.max():.1f}] "
              f"Z[{z.min():.1f}, {z.max():.1f}]")
        
        return output_path
    
    def laz_to_dem(self, laz_path, grid_size=None):
        """
        Convert LAZ point cloud to DEM raster
        
        Args:
            laz_path: Path to LAZ file
            grid_size: Tuple of (width, height) for output grid, or None for auto
        
        Returns:
            Path to DEM GeoTIFF file
        """
        print(f"\nConverting {laz_path.name} to DEM raster...")
        
        try:
            # Read LAZ file
            las = laspy.read(str(laz_path))
            
            x = las.x
            y = las.y
            z = las.z
            
            print(f"  Points: {len(x)}")
            print(f"  X range: [{x.min():.2f}, {x.max():.2f}]")
            print(f"  Y range: [{y.min():.2f}, {y.max():.2f}]")
            print(f"  Z range: [{z.min():.2f}, {z.max():.2f}]")
            
            # Calculate grid dimensions
            x_min, x_max = x.min(), x.max()
            y_min, y_max = y.min(), y.max()
            
            if grid_size is None:
                # Auto-calculate based on resolution
                width = int((x_max - x_min) / self.resolution)
                height = int((y_max - y_min) / self.resolution)
                # Limit to reasonable size
                width = min(width, 2000)
                height = min(height, 2000)
            else:
                width, height = grid_size
            
            print(f"  Creating {width}x{height} grid (resolution: {self.resolution}m)")
            
            # Create grid
            grid_x = np.linspace(x_min, x_max, width)
            grid_y = np.linspace(y_min, y_max, height)
            grid_x, grid_y = np.meshgrid(grid_x, grid_y)
            
            # Interpolate elevation values
            print("  Interpolating elevation values...")
            points = np.column_stack([x, y])
            
            # Use nearest neighbor for speed, or linear for quality
            grid_z = griddata(points, z, (grid_x, grid_y), method='nearest')
            
            # Handle any NaN values
            if np.any(np.isnan(grid_z)):
                print("  Filling NaN values...")
                mask = np.isnan(grid_z)
                grid_z[mask] = np.nanmean(grid_z)
            
            # Save as GeoTIFF
            output_base = laz_path.stem
            geotiff_path = self.output_dir / f"{output_base}_dem.tif"
            
            transform = from_bounds(x_min, y_min, x_max, y_max, width, height)
            
            with rasterio.open(
                geotiff_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=grid_z.dtype,
                crs='+proj=latlong',
                transform=transform,
            ) as dst:
                dst.write(grid_z, 1)
            
            print(f"  Saved GeoTIFF: {geotiff_path}")
            
            # Also save as numpy array for direct use
            npy_path = self.output_dir / f"{output_base}_dem.npy"
            np.save(npy_path, grid_z.astype(np.float32))
            print(f"  Saved numpy array: {npy_path}")
            
            # Save metadata
            meta_path = self.output_dir / f"{output_base}_dem_meta.json"
            metadata = {
                'width': width,
                'height': height,
                'resolution': self.resolution,
                'bounds': {
                    'x_min': float(x_min),
                    'x_max': float(x_max),
                    'y_min': float(y_min),
                    'y_max': float(y_max),
                    'z_min': float(grid_z.min()),
                    'z_max': float(grid_z.max())
                },
                'source_points': len(x),
                'source_file': str(laz_path.name)
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  Saved metadata: {meta_path}")
            
            return geotiff_path, npy_path, metadata
            
        except Exception as e:
            print(f"Error converting LAZ to DEM: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None


def main():
    parser = argparse.ArgumentParser(
        description="Download USGS LiDAR data and convert to DEM raster for line-of-sight analysis"
    )
    parser.add_argument("--lat", type=float, default=39.7392,
                       help="Latitude (default: Denver, CO)")
    parser.add_argument("--lon", type=float, default=-104.9903,
                       help="Longitude (default: Denver, CO)")
    parser.add_argument("--output-dir", default="lidar_data",
                       help="Output directory for downloaded data")
    parser.add_argument("--resolution", type=float, default=1.0,
                       help="DEM resolution in meters (default: 1.0)")
    parser.add_argument("--grid-size", type=int, nargs=2, default=None,
                       help="Fixed grid size as 'width height' (default: auto)")
    parser.add_argument("--sample", action="store_true",
                       help="Create sample data instead of downloading (for testing)")
    
    args = parser.parse_args()
    
    grid_size = tuple(args.grid_size) if args.grid_size else None
    
    fetcher = USGSLidarFetcher(args.lat, args.lon, args.output_dir, args.resolution)
    
    if args.sample:
        # Create sample data for testing
        print("="*60)
        print("CREATING SAMPLE DATA")
        print("="*60)
        laz_file = fetcher.create_sample_laz()
    else:
        # Try to find and download real data
        print("="*60)
        print("SEARCHING FOR USGS DATA")
        print("="*60)
        tiles = fetcher.find_lidar_tiles()
        
        if not tiles:
            print("\nNo data found. Creating sample data instead...")
            laz_file = fetcher.create_sample_laz()
        else:
            print("\nAvailable datasets:")
            for i, tile in enumerate(tiles):
                print(f"{i + 1}. {tile.get('title', 'Unknown')}")
            
            # For this demo, we'll create sample data
            # In a real scenario, you'd download from tile['downloadURL']
            print("\nNote: Actual download requires specific USGS file URLs.")
            print("Creating sample data for demonstration...")
            laz_file = fetcher.create_sample_laz()
    
    # Convert to DEM
    if laz_file:
        print("\n" + "="*60)
        print("CONVERTING TO DEM RASTER")
        print("="*60)
        geotiff_path, npy_path, metadata = fetcher.laz_to_dem(laz_file, grid_size)
        
        if geotiff_path and npy_path:
            print("\n" + "="*60)
            print("SUCCESS!")
            print("="*60)
            print(f"\nDEM files created:")
            print(f"  GeoTIFF: {geotiff_path}")
            print(f"  NumPy:   {npy_path}")
            print(f"  Metadata: {geotiff_path.parent / (geotiff_path.stem + '_meta.json')}")
            print(f"\nDEM Info:")
            print(f"  Size: {metadata['width']}x{metadata['height']} pixels")
            print(f"  Resolution: {metadata['resolution']}m/pixel")
            print(f"  Elevation range: {metadata['bounds']['z_min']:.2f}m to {metadata['bounds']['z_max']:.2f}m")
            print(f"\nUse with los.cpp:")
            print(f"  1. Build: python setup.py build_ext --inplace")
            print(f"  2. Run: python usgs_los_test.py")
            print(f"\nOr in Python:")
            print(f"  import numpy as np")
            print(f"  import los")
            print(f"  dem = np.load('{npy_path}')")
            print(f"  result = los.los_boolean(dem, {metadata['width']}, {metadata['height']}, x0, y0, z0, x1, y1, z1)")


if __name__ == "__main__":
    main()