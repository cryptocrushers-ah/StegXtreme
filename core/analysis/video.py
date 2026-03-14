"""
VideoAnalyzer — steganography detection for video files.

Algorithm:
  1. Sample N evenly-spaced frames from the video.
  2. For each frame compute:
     - LSB noise ratio  : fraction of pixels whose LSB differs from the
       spatial-neighbour prediction (high → possible LSB embedding).
     - DCT AC energy    : mean absolute value of non-DC DCT coefficients
       in 8×8 blocks (unusually uniform → possible DCT domain embedding).
     - Frame-delta variance : change between consecutive sampled frames
       (anomalously low variance can indicate repeated embedding patterns).
  3. Aggregate the per-frame scores into a single probability in [0, 1].
  4. Return a structured result dict.
"""

from __future__ import annotations

import math
import os
from typing import Dict, Any

import cv2
import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _lsb_noise_ratio(gray: np.ndarray) -> float:
    """
    Estimate how 'random' the LSB plane looks compared to a simple
    spatial prediction.  A steganographically modified image tends to
    have a flatter, more-uniform LSB distribution.
    """
    lsb = (gray & 1).astype(np.float32)
    # Horizontal neighbour prediction
    pred = np.roll(lsb, 1, axis=1)
    pred[:, 0] = lsb[:, 0]
    diff = np.abs(lsb - pred)
    return float(diff.mean())


def _dct_ac_energy(gray: np.ndarray) -> float:
    """
    Compute mean absolute AC energy over non-overlapping 8×8 DCT blocks.
    Embedding in the DCT domain slightly alters the AC coefficient
    distribution.
    """
    h, w = gray.shape
    h8, w8 = (h // 8) * 8, (w // 8) * 8
    patch = gray[:h8, :w8].astype(np.float32)
    total, count = 0.0, 0
    for r in range(0, h8, 8):
        for c in range(0, w8, 8):
            block = patch[r:r+8, c:c+8]
            dct_block = cv2.dct(block)
            ac = dct_block.copy()
            ac[0, 0] = 0.0          # zero out DC
            total += float(np.abs(ac).mean())
            count += 1
    return total / max(count, 1)


def _chi_square_lsb(gray: np.ndarray) -> float:
    """
    Chi-square test on the LSB histogram of a grayscale frame.
    Returns a score in [0, 1] where values close to 1 suggest
    artificial uniformity (embedding).
    """
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    # Pair adjacent bins (value 2k and 2k+1); they should be equal if LSBs
    # are manipulated uniformly.
    pairs = hist.reshape(-1, 2)
    expected = pairs.sum(axis=1, keepdims=True) / 2.0
    with np.errstate(divide='ignore', invalid='ignore'):
        chi2 = np.where(expected > 0,
                        (pairs - expected) ** 2 / expected,
                        0.0).sum()
    # Normalise: under H0 the expected value of chi2 is (n_pairs - 1).
    n_pairs = len(pairs)
    normalised = chi2 / max(n_pairs - 1, 1)
    # Lower chi2 → more uniform → higher steganography suspicion
    score = 1.0 / (1.0 + normalised)
    return float(np.clip(score, 0.0, 1.0))


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

class VideoAnalyzer:
    """Detect steganographic content hidden inside a video file."""

    #: Number of frames sampled for analysis (more → slower but more accurate).
    N_FRAMES: int = 16

    @classmethod
    def analyze(cls, video_path: str) -> Dict[str, Any]:
        """
        Analyse *video_path* for signs of steganographic embedding.

        Parameters
        ----------
        video_path : str
            Absolute or relative path to the video file (MP4, AVI, …).

        Returns
        -------
        dict
            {
              "probability": float,      # 0.0 (clean) … 1.0 (likely stego)
              "verdict":     str,        # "CLEAN" | "SUSPICIOUS" | "LIKELY_STEGO"
              "features": {
                "lsb_noise":      float,
                "dct_ac_energy":  float,
                "chi_square_lsb": float,
                "frame_delta_cv": float, # coefficient of variation of frame deltas
              }
            }

        Raises
        ------
        ValueError
            If the file cannot be opened or contains no readable frames.
        """
        if not os.path.isfile(video_path):
            raise ValueError(f"File not found: {video_path!r}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path!r}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            # Some containers don't report frame count; fall back to 1 frame
            total_frames = 1

        n = min(cls.N_FRAMES, total_frames)
        indices = [int(i * total_frames / n) for i in range(n)]

        lsb_scores, dct_scores, chi_scores, deltas = [], [], [], []
        prev_gray: np.ndarray | None = None

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            lsb_scores.append(_lsb_noise_ratio(gray))
            dct_scores.append(_dct_ac_energy(gray))
            chi_scores.append(_chi_square_lsb(gray))

            if prev_gray is not None:
                delta = float(np.abs(gray.astype(np.int32) - prev_gray.astype(np.int32)).mean())
                deltas.append(delta)
            prev_gray = gray

        cap.release()

        if not lsb_scores:
            raise ValueError("No frames could be decoded from the video.")

        feat_lsb = float(np.mean(lsb_scores))
        feat_dct = float(np.mean(dct_scores))
        feat_chi = float(np.mean(chi_scores))

        # Coefficient of variation of frame deltas (low → suspicious)
        if deltas:
            delta_mean = float(np.mean(deltas))
            delta_std  = float(np.std(deltas))
            feat_delta_cv = (delta_std / delta_mean) if delta_mean > 0 else 0.0
            # Invert: low CV is suspicious
            delta_score = 1.0 - min(feat_delta_cv, 1.0)
        else:
            feat_delta_cv = 0.0
            delta_score = 0.0

        # ── Weighted aggregate ─────────────────────────────────────────────
        # lsb_noise: lower ratio indicates more uniform bits → suspicious
        lsb_score = 1.0 - feat_lsb              # 0.5 noise ratio → 0.5 score

        # dct: normalise against a typical "natural" level ~5–15
        dct_norm = math.exp(-feat_dct / 20.0)   # high energy → low score

        probability = float(np.clip(
            0.35 * lsb_score +
            0.25 * feat_chi  +
            0.20 * dct_norm  +
            0.20 * delta_score,
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
                "lsb_noise":      round(feat_lsb, 4),
                "dct_ac_energy":  round(feat_dct, 4),
                "chi_square_lsb": round(feat_chi, 4),
                "frame_delta_cv": round(feat_delta_cv, 4),
            },
        }
