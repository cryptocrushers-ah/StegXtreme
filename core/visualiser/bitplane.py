import matplotlib  # type: ignore
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # type: ignore
import numpy as np  # type: ignore
from core.visualiser.renderer import render_fig_base64  # type: ignore

def render_bitplanes(frame: np.ndarray) -> str:
    """
    Renders the 8 bit-planes of the Y (luminance) channel of a frame
    into a single plot and returns it as a base64 PNG.
    """
    if len(frame.shape) == 3:
        # Convert to Grayscale manually if it is RGB/BGR
        # Using standard luma weights: Y = 0.299R + 0.587G + 0.114B
        if frame.shape[2] == 3:
            y_channel = np.dot(frame[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        else:
            y_channel = frame[..., 0] # fallback
    else:
        y_channel = frame

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle("8 Bit-Planes of Luminance (Y) Channel", fontsize=16)

    for i, ax in enumerate(axes.flat):
        # Extract the i-th bitplane: move bit i to the 0th position and mask LSB
        bitplane = (y_channel >> i) & 1
        # Multiply by 255 for visibility in plot 
        ax.imshow(bitplane * 255, cmap="gray", vmin=0, vmax=255)
        ax.set_title(f"Bit-Plane {i} (0=LSB, 7=MSB)", fontsize=12)
        ax.axis('off')

    plt.tight_layout()
    return render_fig_base64(fig)
