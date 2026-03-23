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

    from concurrent.futures import ThreadPoolExecutor

    def _process_frame_wavelet(frame_tuple: tuple[int, np.ndarray]) -> tuple[int, float, float, float]:
        idx, frame = frame_tuple
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(float)
        _, (LH, HL, _) = pywt.dwt2(gray, 'haar')
        return idx, idx / video_fps, float(np.var(LH)), float(np.var(HL))

    frames_to_process = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frames_to_process.append((idx, frame))
    cap.release()

    if not frames_to_process:
        raise ValueError("No frames could be read from video.")

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(_process_frame_wavelet, frames_to_process))

    # Sort results by index to keep time order
    results.sort(key=lambda x: x[0])
    timestamps = [r[1] for r in results]
    lh_variances = [r[2] for r in results]
    hl_variances = [r[3] for r in results]

    if not timestamps:
        raise ValueError("No frames could be read from video.")

    # Combine variances
    combined_variance = np.array(lh_variances) + np.array(hl_variances)

    # Plot Timeline Heatmap strip
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 3))
    
    # Reshape combined variance to 1xN for imshow
    strip = combined_variance.reshape(1, -1)
    
    cax = ax.imshow(strip, aspect='auto', cmap='magma', extent=[timestamps[0], timestamps[-1], 0, 1])
    
    ax.set_yticks([])
    ax.set_title("Neural Wavelet Frequency Timeline (Magma = Forensic Variance)", fontsize=14, color='#00ffe0', fontweight='bold')
    ax.set_xlabel("Time (seconds)", fontsize=12, color='#94a3b8')
    
    fig.colorbar(cax, orientation='horizontal', pad=0.35, label='Signal Variance Density')

    plt.tight_layout()
    return render_fig_base64(fig)
