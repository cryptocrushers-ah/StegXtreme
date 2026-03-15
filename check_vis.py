import cv2
import numpy as np
import os
from core.visualiser.bitplane import render_bitplanes

# Create a dummy image
img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

# Render bit-planes
b64 = render_bitplanes(img)

# Print the first 100 chars of the base64 string
print(b64[:100])

# Extract base64 part
header, data = b64.split(',', 1)
import base64 as b64_mod
with open("vis_output.png", "wb") as f:
    f.write(b64_mod.b64decode(data))

print("Saved to vis_output.png")
