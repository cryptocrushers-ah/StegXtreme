import base64
import cv2  # type: ignore
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from core.visualiser.renderer import render_fig_base64  # type: ignore

def render_bitplanes(frame: np.ndarray) -> str:
    """
    Renders 8 LSB bitplanes of an image as a single 2x4 grid image,
    returned as a base64 string.
    """
    if len(frame.shape) == 3:
        # Convert to grayscale for bitplane visualization
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Create figure
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle("8 Bit-Planes of Luminance (Y) Channel", fontsize=20, fontweight='bold', y=0.95)

    for i in range(8):
        # Extract the i-th bit
        plane = (gray >> i) & 1
        
        # Plot in grid
        ax = axes[i // 4, i % 4]
        ax.imshow(plane, cmap='gray')
        ax.set_title(f"Bit-Plane {i} (0=LSB, 7=MSB)", fontsize=12)
        ax.axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.92])
    return render_fig_base64(fig)
