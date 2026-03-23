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

    import pywt
    # Extract standard LSB
    lsb = (gray & 1).astype(float)

    # Perform 2D Wavelet Transform (Haar)
    coeffs2 = pywt.dwt2(lsb, 'haar')
    LL, (LH, HL, HH) = coeffs2
    
    # Combined high-frequency components
    # HH is diagonal, LH is horizontal, HL is vertical
    magnitude = np.sqrt(LH**2 + HL**2 + HH**2)
    
    # Scale up magnitude to original size for visualization
    magnitude_resized = cv2.resize(magnitude, (gray.shape[1], gray.shape[0]))

    # Render with professional dark theme
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(magnitude_resized, cmap='magma', interpolation='bilinear')
    ax.set_title("Neural Wavelet Heatmap", fontsize=14, color='#00ffe0', fontweight='bold')
    fig.colorbar(cax, orientation='vertical', label='Signal Variance Density')
    ax.axis('off')
    
    plt.tight_layout()
    return render_fig_base64(fig)
