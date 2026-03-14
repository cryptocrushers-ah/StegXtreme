import matplotlib  # type: ignore
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # type: ignore
import pywt  # type: ignore
import numpy as np  # type: ignore
from core.visualiser.renderer import render_fig_base64  # type: ignore

def render_heatmap(frame: np.ndarray) -> str:
    """
    Computes a 2D Discrete Wavelet Transform (Haar) on the frame and 
    renders the high-frequency subbands (LH, HL, HH) as false-color heatmaps
    to highlight steganographic noise.
    """
    if len(frame.shape) == 3:
        if frame.shape[2] == 3:
            gray = np.dot(frame[..., :3], [0.2989, 0.5870, 0.1140]).astype(float)
        else:
            gray = frame[..., 0].astype(float)
    else:
        gray = frame.astype(float)

    # 2D Haar Wavelet Transform
    coeffs = pywt.dwt2(gray, 'haar')
    LL, (LH, HL, HH) = coeffs

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle("Haar Wavelet Subbands", fontsize=16)

    # Convert to log scale for better visualization of noise clusters
    def normalize(subband):
        abs_val = np.abs(subband)
        return np.log1p(abs_val)

    # Plot Configuration
    axes[0, 0].imshow(LL, cmap='gray')
    axes[0, 0].set_title("LL (Approximation)")
    axes[0, 0].axis('off')

    # Jet is excellent for false-colour heatmaps (blue=low, red=high)
    im_lh = axes[0, 1].imshow(normalize(LH), cmap='jet')
    axes[0, 1].set_title("LH (Vertical Details)")
    axes[0, 1].axis('off')
    fig.colorbar(im_lh, ax=axes[0, 1], shrink=0.8)

    im_hl = axes[1, 0].imshow(normalize(HL), cmap='jet')
    axes[1, 0].set_title("HL (Horizontal Details)")
    axes[1, 0].axis('off')
    fig.colorbar(im_hl, ax=axes[1, 0], shrink=0.8)

    im_hh = axes[1, 1].imshow(normalize(HH), cmap='jet')
    axes[1, 1].set_title("HH (Diagonal Details)")
    axes[1, 1].axis('off')
    fig.colorbar(im_hh, ax=axes[1, 1], shrink=0.8)

    plt.tight_layout()
    return render_fig_base64(fig)
