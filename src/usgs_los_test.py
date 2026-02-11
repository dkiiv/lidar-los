#!/usr/bin/env python3
"""
USGS LiDAR Line-of-Sight Test
Tests line-of-sight analysis using real or sample USGS LiDAR data

Usage:
    python usgs_los_test.py
    python usgs_los_test.py --dem lidar_data/sample_lidar_39.7392_-104.9903_dem.npy
"""

import numpy as np
import argparse
import json
from pathlib import Path

try:
    import los
except ImportError:
    print("Error: los module not found!")
    print("Build it first with: python setup.py build_ext --inplace")
    exit(1)


def find_latest_dem(data_dir="lidar_data"):
    """Find the most recently created DEM file"""
    data_path = Path(data_dir)
    if not data_path.exists():
        return None
    
    npy_files = list(data_path.glob("*_dem.npy"))
    if not npy_files:
        return None
    
    # Sort by modification time, newest first
    npy_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return npy_files[0]


def load_dem_with_metadata(dem_path):
    """Load DEM and its metadata"""
    dem = np.load(str(dem_path))
    
    # Try to load metadata
    meta_path = dem_path.parent / f"{dem_path.stem}_meta.json"
    metadata = None
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            metadata = json.load(f)
    
    return dem, metadata


def los_boolean_test(dem, width, height, x0, y0, z0, x1, y1, z1):
    """Wrapper for los.los_boolean with error handling"""
    try:
        result = los.los_boolean(
            dem,
            width,
            height,
            x0, y0, z0,
            x1, y1, z1
        )
        return result
    except Exception as e:
        print(f"Error in los_boolean: {e}")
        return None


def los_probability_test(dem, width, height, x0, y0, z0, x1, y1, z1):
    """Wrapper for los.los_probability with error handling"""
    try:
        result = los.los_probability(
            dem,
            width,
            height,
            x0, y0, z0,
            x1, y1, z1
        )
        return result
    except Exception as e:
        print(f"Error in los_probability: {e}")
        return None


def print_test_header(test_num, description):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"Test {test_num}: {description}")
    print('='*60)


def main():
    parser = argparse.ArgumentParser(description="Test LOS with USGS LiDAR data")
    parser.add_argument("--dem", type=str, default=None,
                       help="Path to DEM .npy file (default: auto-detect latest)")
    parser.add_argument("--data-dir", type=str, default="lidar_data",
                       help="Directory containing DEM files")
    
    args = parser.parse_args()
    
    # Find or use specified DEM file
    if args.dem:
        dem_path = Path(args.dem)
    else:
        dem_path = find_latest_dem(args.data_dir)
        if dem_path is None:
            print(f"No DEM files found in {args.data_dir}/")
            print("Run fetch_usgs_lidar.py first:")
            print("  python fetch_usgs_lidar.py --sample")
            return
    
    if not dem_path.exists():
        print(f"DEM file not found: {dem_path}")
        return
    
    print("="*60)
    print("USGS LiDAR Line-of-Sight Test")
    print("="*60)
    print(f"Loading DEM: {dem_path}")
    
    # Load DEM and metadata
    dem, metadata = load_dem_with_metadata(dem_path)
    
    # Ensure contiguous array
    dem = np.ascontiguousarray(dem, dtype=np.float32)
    
    height, width = dem.shape
    
    print(f"DEM size: {width}x{height}")
    print(f"Elevation range: {dem.min():.2f}m to {dem.max():.2f}m")
    
    if metadata:
        print(f"Resolution: {metadata.get('resolution', 'unknown')}m/pixel")
        print(f"Source points: {metadata.get('source_points', 'unknown')}")
    
    # Define test points based on DEM size
    # Place points away from edges
    margin = max(width, height) // 10
    
    # Observer in lower-left quadrant
    x0 = float(margin)
    y0 = float(margin)
    z0 = float(dem[int(y0), int(x0)] + 2.0)  # 2m above ground
    
    # Target in upper-right quadrant
    x1 = float(width - margin)
    y1 = float(height - margin)
    z1 = float(dem[int(y1), int(x1)] + 2.0)  # 2m above ground
    
    print(f"\nObserver: ({x0:.1f}, {y0:.1f}, {z0:.1f})")
    print(f"Target:   ({x1:.1f}, {y1:.1f}, {z1:.1f})")
    
    # Test 1: Ground level to ground level (likely blocked by terrain)
    print_test_header(1, "Ground level LOS (2m above surface)")
    result = los_boolean_test(dem, width, height, x0, y0, z0, x1, y1, z1)
    if result is not None:
        print(f"LOS visible: {result}")
        prob = los_probability_test(dem, width, height, x0, y0, z0, x1, y1, z1)
        if prob is not None:
            print(f"LOS probability: {prob:.4f}")
    
    # Test 2: Elevated observer and target (more likely to see over terrain)
    print_test_header(2, "Elevated LOS (20m above surface)")
    z0_elevated = float(dem[int(y0), int(x0)] + 20.0)
    z1_elevated = float(dem[int(y1), int(x1)] + 20.0)
    
    print(f"Observer: ({x0:.1f}, {y0:.1f}, {z0_elevated:.1f})")
    print(f"Target:   ({x1:.1f}, {y1:.1f}, {z1_elevated:.1f})")
    
    result = los_boolean_test(dem, width, height, x0, y0, z0_elevated, x1, y1, z1_elevated)
    if result is not None:
        print(f"LOS visible: {result}")
        prob = los_probability_test(dem, width, height, x0, y0, z0_elevated, x1, y1, z1_elevated)
        if prob is not None:
            print(f"LOS probability: {prob:.4f}")
    
    # Test 3: Short distance LOS (nearby points, usually visible)
    print_test_header(3, "Short distance LOS")
    x0_short = float(width // 2)
    y0_short = float(height // 2)
    z0_short = float(dem[int(y0_short), int(x0_short)] + 2.0)
    
    x1_short = float(width // 2 + 10)
    y1_short = float(height // 2 + 10)
    z1_short = float(dem[min(int(y1_short), height-1), min(int(x1_short), width-1)] + 2.0)
    
    print(f"Observer: ({x0_short:.1f}, {y0_short:.1f}, {z0_short:.1f})")
    print(f"Target:   ({x1_short:.1f}, {y1_short:.1f}, {z1_short:.1f})")
    
    result = los_boolean_test(dem, width, height, x0_short, y0_short, z0_short, 
                              x1_short, y1_short, z1_short)
    if result is not None:
        print(f"LOS visible: {result}")
        prob = los_probability_test(dem, width, height, x0_short, y0_short, z0_short,
                                    x1_short, y1_short, z1_short)
        if prob is not None:
            print(f"LOS probability: {prob:.4f}")
    
    # Test 4: Find highest and lowest points
    print_test_header(4, "Peak to valley LOS")
    
    max_idx = np.unravel_index(np.argmax(dem), dem.shape)
    min_idx = np.unravel_index(np.argmin(dem), dem.shape)
    
    x0_peak = float(max_idx[1])
    y0_peak = float(max_idx[0])
    z0_peak = float(dem[max_idx] + 2.0)
    
    x1_valley = float(min_idx[1])
    y1_valley = float(min_idx[0])
    z1_valley = float(dem[min_idx] + 2.0)
    
    print(f"Peak:   ({x0_peak:.1f}, {y0_peak:.1f}, {z0_peak:.1f})")
    print(f"Valley: ({x1_valley:.1f}, {y1_valley:.1f}, {z1_valley:.1f})")
    
    result = los_boolean_test(dem, width, height, x0_peak, y0_peak, z0_peak,
                              x1_valley, y1_valley, z1_valley)
    if result is not None:
        print(f"LOS visible: {result}")
        prob = los_probability_test(dem, width, height, x0_peak, y0_peak, z0_peak,
                                    x1_valley, y1_valley, z1_valley)
        if prob is not None:
            print(f"LOS probability: {prob:.4f}")
    
    print("\n" + "="*60)
    print("Tests complete!")
    print("="*60)


if __name__ == "__main__":
    main()