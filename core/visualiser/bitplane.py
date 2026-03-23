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

    # Create figure with dark theme
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle("Neural Bit-Plane Decomposition (Y-Channel Layers)", 
                 fontsize=22, fontweight='bold', y=0.98, color='#00ffe0')

    for i in range(8):
        # Extract the i-th bit
        plane = (gray >> i) & 1
        
        # Plot in grid
        ax = axes[i // 4, i % 4]
        ax.imshow(plane, cmap='gray', interpolation='nearest')
        ax.set_title(f"LAYER {i} {'(LSB)' if i==0 else '(MSB)' if i==7 else ''}", 
                     fontsize=14, color='#94a3b8', fontweight='bold')
        ax.axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return render_fig_base64(fig)
