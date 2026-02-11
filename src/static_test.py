import numpy as np
import los

def los_runtime():
    return los.los_boolean(
      dem,
      dem.shape[1],
      dem.shape[0],
      x0, y0, z0,
      x1, y1, z1
    )

# Grid size
width = 1000
height = 1000

# Create flat DEM at 0m
dem = np.zeros((height, width), dtype=np.float32)
dem = np.ascontiguousarray(dem)

# Observer positions
x0, y0, z0 = 100.0, 100.0, 10.0
x1, y1, z1 = 900.0, 900.0, 10.0

print("=== Test 1: Flat terrain (should be visible) ===")
print("LOS?:", los_runtime())

# Add hill in the middle
dem[500, 500] = 50.0
print("\n=== Test 2: Add blocking hill (should be blocked) ===")
print("LOS?:", los_runtime())

z0, z1 = 100.0, 100.0
print("\n=== Test 3: Raise observers above hill (should be visible) ===")
print("LOS?:", los_runtime())