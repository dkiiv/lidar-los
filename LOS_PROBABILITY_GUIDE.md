# Line-of-Sight Probability Function

## Overview
The `los_probability` function has been added to `los.cpp` to provide a more nuanced line-of-sight metric beyond the binary yes/no of `los_boolean`.

## How It Works

Instead of checking a single ray, `los_probability` samples **multiple rays** in a grid pattern around the primary line of sight and returns the fraction that have clear visibility.

### Algorithm

1. **Grid Sampling Pattern**
   - Samples are arranged in a grid around both the observer and target positions
   - Default: 9 samples (3x3 grid)
   - Configurable via `num_samples` parameter

2. **Offset Calculation**
   - Samples are spread ±2 grid cells from the center point
   - Each endpoint gets the same offset to maintain parallel rays

3. **Probability Calculation**
   ```
   probability = (successful_rays / total_rays)
   ```

## Usage

### Python API

```python
import numpy as np
import los

# Load DEM
dem = np.load('lidar_data/sample_lidar_39.7392_-104.9903_dem.npy')
width, height = dem.shape[1], dem.shape[0]

# Define observer and target
x0, y0, z0 = 100.0, 100.0, 10.0
x1, y1, z1 = 900.0, 900.0, 10.0

# Get probability (default 9 samples)
prob = los.los_probability(dem, width, height, x0, y0, z0, x1, y1, z1)
print(f"LOS Probability: {prob:.2%}")

# Use more samples for higher precision
prob_detailed = los.los_probability(dem, width, height, x0, y0, z0, x1, y1, z1, num_samples=25)
print(f"LOS Probability (25 samples): {prob_detailed:.2%}")
```

## Return Values

- **1.0** - All sampled rays have clear line of sight (high confidence)
- **0.5** - Half of sampled rays are blocked (marginal/uncertain)
- **0.0** - All sampled rays are blocked (no line of sight)

## Interpretation

### High Probability (0.8 - 1.0)
- Strong line of sight
- Clear path with good margin
- Observer and target have multiple viable sight lines

### Medium Probability (0.3 - 0.7)
- Marginal line of sight
- Terrain comes close to blocking
- May be affected by small position changes or terrain uncertainty

### Low Probability (0.0 - 0.2)
- Poor or no line of sight
- Significant terrain obstruction
- Only grazing paths, if any

## Sample Patterns

### 9 Samples (3x3 grid)
```
[7] [8] [9]
[4] [5] [6]
[1] [2] [3]
```

### 25 Samples (5x5 grid)
```
[21][22][23][24][25]
[16][17][18][19][20]
[11][12][13][14][15]
[6] [7] [8] [9] [10]
[1] [2] [3] [4] [5]
```

## Use Cases

1. **Uncertainty Quantification**
   - Account for DEM resolution limitations
   - Handle position uncertainty in GPS coordinates

2. **Quality Metric**
   - Distinguish between "barely visible" and "wide open" sight lines
   - Useful for optimal positioning

3. **Robust Analysis**
   - Less sensitive to single-pixel artifacts in DEM
   - Smoother results near terrain edges

## Performance

- Time complexity: O(num_samples × ray_length)
- Default 9 samples: ~9x slower than `los_boolean`
- For performance-critical code, use `los_boolean` for binary checks

## Example Output

```python
# Test case: Observer at 100m elevation looking across valley

# Ground level check
print(los.los_boolean(dem, w, h, x0, y0, 100, x1, y1, 105))
# Output: 0.0 (blocked)

print(los.los_probability(dem, w, h, x0, y0, 100, x1, y1, 105))
# Output: 0.22 (mostly blocked, some grazing rays succeed)

# Elevated check
print(los.los_boolean(dem, w, h, x0, y0, 150, x1, y1, 155))
# Output: 1.0 (visible)

print(los.los_probability(dem, w, h, x0, y0, 150, x1, y1, 155))
# Output: 1.0 (all rays clear)
```

## Recommended num_samples Values

- **1**: Same as `los_boolean` (no sampling)
- **9**: Good default (3x3 grid, fast)
- **25**: Higher precision (5x5 grid, moderate speed)
- **49**: Very high precision (7x7 grid, slower)
- **100**: Maximum precision (10x10 grid, slowest)

Choose based on your accuracy vs. performance requirements.