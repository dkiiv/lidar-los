import numpy as np
import los

# Create fake DEM for example
width = 1000
height = 1000
cell_size = 1.0

dem = np.zeros((height, width), dtype=np.float32)

# Add a hill in the middle
dem[500, 500] = 50.0

origin_x = 0.0
origin_y = 0.0

# Two world points
x0, y0, z0 = 100.0, 100.0, 10.0
x1, y1, z1 = 900.0, 900.0, 10.0

p = los.los_probability(
  dem,
  origin_x,
  origin_y,
  cell_size,
  x0, y0, z0,
  x1, y1, z1
)

print("LOS probability:", p)