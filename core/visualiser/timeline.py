import matplotlib  # type: ignore
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # type: ignore
import cv2  # type: ignore
import pywt  # type: ignore
import numpy as np  # type: ignore
import os
from core.visualiser.renderer import render_fig_base64  # type: ignore

def render_timeline(video_path: str, n_frames: int = 30) -> str:
    """
    Extracts n_frames across a video, computes the variance of LH and HL wavelet 
    subbands per frame, and plots a timeline indicating suspicious high-noise regions.
    """
    if not os.path.isfile(video_path):
        raise ValueError(f"Video file not found: {video_path}")

    # Read video metadata
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    
    # Calculate uniform sampling intervals
    if total_frames <= n_frames:
        frame_indices = list(range(total_frames))
    else:
        frame_indices = np.linspace(0, total_frames - 1, n_frames, dtype=int).tolist()

    timestamps = []
    lh_variances = []
    hl_variances = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            break

        # Record timestamp (in seconds)
        timestamps.append(idx / video_fps)  # type: ignore

        # Convert to Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)
        
        # Haar Wavelet
        _, (LH, HL, _) = pywt.dwt2(gray, 'haar')
        
        # Store variance
        lh_variances.append(np.var(LH))
        hl_variances.append(np.var(HL))

    cap.release()

    if not timestamps:
        raise ValueError("No frames could be read from video.")

    # Combine variances
    combined_variance = np.array(lh_variances) + np.array(hl_variances)

    # Plot Timeline Heatmap strip
    # We create a 1D array heatmap
    fig, ax = plt.subplots(figsize=(12, 3))
    
    # Reshape combined variance to 1xN for imshow
    strip = combined_variance.reshape(1, -1)
    
    cax = ax.imshow(strip, aspect='auto', cmap='jet', extent=[timestamps[0], timestamps[-1], 0, 1])
    
    ax.set_yticks([])
    ax.set_title("Wavelet High-Frequency Variance Timeline (Red = High Noise / Suspect)", fontsize=14)
    ax.set_xlabel("Time (seconds)", fontsize=12)
    
    fig.colorbar(cax, orientation='horizontal', pad=0.3, label='LH + HL Variance')

    plt.tight_layout()
    return render_fig_base64(fig)
