import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2  # type: ignore
import numpy as np  # type: ignore
from core.visualiser.renderer import render_fig_base64

def render_heatmap(frame: np.ndarray) -> str:
    """
    Renders a heatmap of the absolute difference between adjacent pixels in the LSBs,
    indicating potential anomalous regions, returned as a base64 string.
    """
    if len(frame.shape) == 3:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # Extract standard LSB
    lsb = gray & 1

    # Compute a simple difference heatmap (gradient of LSBs)
    grad_x = cv2.Sobel(lsb, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(lsb, cv2.CV_64F, 0, 1, ksize=3)
    
    # Magnitude
    magnitude = cv2.magnitude(grad_x, grad_y)
    
    # Render with matplotlib
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(magnitude, cmap='turbo', interpolation='nearest')
    ax.set_title("LSB Noise Heatmap", fontsize=14)
    fig.colorbar(cax, orientation='vertical', label='LSB Gradient Magnitude')
    ax.axis('off')
    
    plt.tight_layout()
    return render_fig_base64(fig)
