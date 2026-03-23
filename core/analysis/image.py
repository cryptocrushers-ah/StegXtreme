"""
ImageAnalyzer — steganography detection for image files.
"""

from __future__ import annotations

import os
from typing import Dict, Any

import numpy as np  # type: ignore[import-untyped]
from PIL import Image  # type: ignore[import-untyped]
from scipy.stats import chi2 as chi2_dist


# ──────────────────────────────────────────────────────────────────────────────
# Per-channel helpers
# ──────────────────────────────────────────────────────────────────────────────

def _chi_square_score(channel: np.ndarray) -> float:
    """
    Chi-square test on the histogram of *channel*.
    Flags artificial uniformity (embedding).
    Score = p_value, but only if it's extremely high (>0.999).
    """
    hist = np.bincount(channel.ravel(), minlength=256).astype(np.float64)
    pairs = hist.reshape(-1, 2)
    observed = pairs
    expected = pairs.sum(axis=1, keepdims=True) / 2.0
    
    with np.errstate(divide='ignore', invalid='ignore'):
        chi2_val = np.where(expected > 1.0,
                            (observed - expected) ** 2 / expected,
                            0.0).sum()
    
    dof = len(pairs) - 1
    p_value = float(chi2_dist.sf(chi2_val, dof))
    # Natural images can have high p-values by chance if they are low-detail.
    # We only flag if it's practically 1.0 (perfectly uniform).
    score = np.clip((p_value - 0.995) / 0.005, 0.0, 1.0)
    return float(score)


def _sample_pairs_score(channel: np.ndarray) -> float:
    """
    Task 2: Fix LSB Noise Threshold.
    Only flag if the ratio is EXTREMELY close to 0.5.
    """
    lsb = channel & 1
    ratio = float(lsb.mean())
    # Natural images are often in the 0.48-0.52 range.
    # Wider tolerance window (0.02) before flagging suspicion.
    dev = abs(ratio - 0.5)
    score = 1.0 - np.clip(dev * 80.0, 0.0, 1.0)
    return float(score)


def _lsb_entropy(channel: np.ndarray) -> float:
    # Shannon entropy of the LSB bitplane.
    # Extremly strict threshold for entropy (0.99999) to avoid natural noise.
    lsb = channel & 1
    p1 = float(lsb.mean())
    p0 = 1.0 - p1
    eps = 1e-12
    entropy = -(p1 * np.log2(p1 + eps) + p0 * np.log2(p0 + eps))
    score = np.clip((entropy - 0.999) / 0.001, 0.0, 1.0)
    return float(score)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

class ImageAnalyzer:
    """Detect steganographic content hidden inside an image file."""

    @classmethod
    def analyze(cls, image_path: str) -> Dict[str, Any]:
        if not os.path.isfile(image_path):
            raise ValueError(f"File not found: {image_path!r}")

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Cannot open image: {exc}") from exc

        arr = np.array(img, dtype=np.uint8)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        from concurrent.futures import ThreadPoolExecutor

        # Parallelize expensive channel analysis
        with ThreadPoolExecutor() as executor:
            # Chi-square per channel
            chi_futures = [executor.submit(_chi_square_score, c) for c in [r, g, b]]
            # Gray-scale heuristics
            gray_arr = np.array(img.convert("L"), dtype=np.uint8)
            sp_future = executor.submit(_sample_pairs_score, gray_arr)
            lsb_future = executor.submit(_lsb_entropy, gray_arr)

            chi_r, chi_g, chi_b = [f.result() for f in chi_futures]
            sp_score = sp_future.result()
            lsb_ent = lsb_future.result()

        chi_mean = (chi_r + chi_g + chi_b) / 3.0

        # Cyber-Efficiency Calibrated Weights:
        # High-priority on Chi-square (histograms), lower on Entropy false-positives.
        probability = float(np.clip(
            0.80 * chi_mean +
            0.10 * sp_score +
            0.10 * lsb_ent,
            0.0, 1.0
        ))

        if probability <= 0.20:
            verdict = "CLEAN"
        elif probability <= 0.55:
            verdict = "SUSPICIOUS"
        else:
            verdict = "LIKELY_STEGO"

        return {
            "probability": round(probability, 4),
            "verdict": verdict,
            "features": {
                "chi_square_r": round(chi_r, 4),
                "chi_square_g": round(chi_g, 4),
                "chi_square_b": round(chi_b, 4),
                "sample_pairs": round(sp_score, 4),
                "lsb_entropy":  round(lsb_ent, 4),
            },
        }
