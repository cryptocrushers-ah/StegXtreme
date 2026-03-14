"""
ImageAnalyzer — steganography detection for image files.

Algorithm:
  1. Chi-square test on paired histogram bins of each colour channel's
     LSB plane (the classic chi² steganalysis).
  2. Sample Pairs (SP) analysis: a lightweight RS-style detector that
     computes the ratio of neighbour-pairs whose difference is odd vs even.
  3. Entropy of the LSB bitplane compared to expected (0.99–1.0 for natural
     images, closer to 1.0 is suspicious).
  4. Combine scores into a single probability in [0, 1].
"""

from __future__ import annotations

import os
from typing import Dict, Any

import numpy as np
from PIL import Image


# ──────────────────────────────────────────────────────────────────────────────
# Per-channel helpers
# ──────────────────────────────────────────────────────────────────────────────

def _chi_square_score(channel: np.ndarray) -> float:
    """
    Chi-square test on the histogram of *channel*.

    Adjacent grey-levels (2k, 2k+1) are paired; under LSB embedding their
    frequencies become equal.  Returns a score in [0, 1] where 1 means
    maximally suspicious.
    """
    hist = np.bincount(channel.ravel(), minlength=256).astype(np.float64)
    pairs = hist.reshape(-1, 2)                 # shape (128, 2)
    expected = pairs.sum(axis=1, keepdims=True) / 2.0
    with np.errstate(divide='ignore', invalid='ignore'):
        chi2 = np.where(expected > 0,
                        (pairs - expected) ** 2 / expected,
                        0.0).sum()
    # Under H0, chi2 ~ χ²(127); normalise by degrees of freedom
    dof = pairs.shape[0] - 1                    # 127
    # Low chi2 → very uniform pairs → suspicious
    normalised = chi2 / max(dof, 1)
    score = 1.0 / (1.0 + normalised)
    return float(np.clip(score, 0.0, 1.0))


def _sample_pairs_score(channel: np.ndarray) -> float:
    """
    Sample Pairs (SP) analysis.  Considers horizontal neighbours (x, y).
    If |x - y| is odd, the pair is *discordant* — embedding tends to increase
    the fraction of discordant pairs.
    Returns a score in [0, 1].
    """
    flat = channel.ravel()
    a = flat[:-1].astype(np.int32)
    b = flat[1:].astype(np.int32)
    diff = np.abs(a - b)
    odd_ratio = float((diff % 2 == 1).mean())
    # Natural images have odd_ratio ≈ 0.5; embedding pushes it higher
    score = np.clip((odd_ratio - 0.5) * 4, 0.0, 1.0)
    return float(score)


def _lsb_entropy(channel: np.ndarray) -> float:
    """
    Shannon entropy of the LSB bitplane.  For a natural image this is
    slightly below 1.0; perfect randomness (embedding) pushes it to 1.0.
    Returns a score in [0, 1].
    """
    lsb = channel & 1
    p1 = float(lsb.mean())
    p0 = 1.0 - p1
    eps = 1e-12
    entropy = -(p1 * np.log2(p1 + eps) + p0 * np.log2(p0 + eps))
    # Normalise: max entropy = 1.0 bit
    score = np.clip(entropy, 0.0, 1.0)
    # Score close to 1.0 is suspicious
    return float(score)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

class ImageAnalyzer:
    """Detect steganographic content hidden inside an image file."""

    @classmethod
    def analyze(cls, image_path: str) -> Dict[str, Any]:
        """
        Analyse *image_path* for signs of steganographic embedding.

        Parameters
        ----------
        image_path : str
            Path to the image file (PNG, BMP, TIFF, …).

        Returns
        -------
        dict
            {
              "probability": float,   # 0.0 (clean) … 1.0 (likely stego)
              "verdict":     str,     # "CLEAN" | "SUSPICIOUS" | "LIKELY_STEGO"
              "features": {
                "chi_square_r":   float,
                "chi_square_g":   float,
                "chi_square_b":   float,
                "sample_pairs":   float,
                "lsb_entropy":    float,
              }
            }

        Raises
        ------
        ValueError
            If the file cannot be opened.
        """
        if not os.path.isfile(image_path):
            raise ValueError(f"File not found: {image_path!r}")

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Cannot open image: {exc}") from exc

        arr = np.array(img, dtype=np.uint8)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        chi_r = _chi_square_score(r)
        chi_g = _chi_square_score(g)
        chi_b = _chi_square_score(b)
        chi_mean = (chi_r + chi_g + chi_b) / 3.0

        # Use all-channel flattened array for SP and entropy
        gray_arr = np.array(img.convert("L"), dtype=np.uint8)
        sp_score  = _sample_pairs_score(gray_arr)
        lsb_ent   = _lsb_entropy(gray_arr)

        probability = float(np.clip(
            0.45 * chi_mean +
            0.30 * sp_score +
            0.25 * lsb_ent,
            0.0, 1.0
        ))

        if probability < 0.35:
            verdict = "CLEAN"
        elif probability < 0.65:
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
