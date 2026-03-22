"""
VideoAnalyzer — steganography detection for video files.
"""

from __future__ import annotations

import math
import os
from typing import Dict, Any

import cv2  # type: ignore[import-untyped]
import numpy as np  # type: ignore[import-untyped]
from scipy.stats import chi2 as chi2_dist


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _lsb_noise_ratio(gray: np.ndarray) -> float:
    """
    Estimate how 'random' the LSB plane looks compared to a simple
    spatial prediction.
    """
    lsb = (gray & 1).astype(np.float32)
    pred = np.roll(lsb, 1, axis=1)
    pred[:, 0] = lsb[:, 0]
    diff = np.abs(lsb - pred)
    return float(diff.mean())


def _dct_ac_energy(gray: np.ndarray) -> float:
    """
    Compute mean absolute AC energy over non-overlapping 8×8 DCT blocks.
    """
    h, w = gray.shape
    h8, w8 = (h // 8) * 8, (w // 8) * 8
    patch = gray[:h8, :w8].astype(np.float32)

    def _block_ac_energy(r: int, c: int) -> float:
        block = patch[r:r+8, c:c+8]
        dct_block = cv2.dct(block)
        ac = dct_block.copy()
        ac[0, 0] = 0.0          # zero out DC
        return float(np.abs(ac).mean())

    energies = [
        _block_ac_energy(r, c)
        for r in range(0, h8, 8)
        for c in range(0, w8, 8)
    ]
    return sum(energies) / max(len(energies), 1)


def _chi_square_lsb(gray: np.ndarray) -> float:
    """
    Chi-square test on the LSB histogram of a grayscale frame.
    Flags artificial uniformity (embedding).
    Score = p_value, but only if it's extremely high (>0.999).
    """
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    pairs = hist.reshape(-1, 2)
    observed = pairs
    expected = pairs.sum(axis=1, keepdims=True) / 2.0
    
    with np.errstate(divide='ignore', invalid='ignore'):
        chi2_val = np.where(expected > 1.0,
                            (observed - expected) ** 2 / expected,
                            0.0).sum()
    
    dof = len(pairs) - 1
    p_value = float(chi2_dist.sf(chi2_val, dof))
    # Natural variations often yield high p-values. Flag only extreme proximity.
    score = np.clip((p_value - 0.999) / 0.001, 0.0, 1.0)
    return float(score)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

class VideoAnalyzer:
    """Detect steganographic content hidden inside a video file."""

    #: Number of frames sampled for analysis.
    N_FRAMES: int = 16

    @classmethod
    def analyze(cls, video_path: str) -> Dict[str, Any]:
        if not os.path.isfile(video_path):
            raise ValueError(f"File not found: {video_path!r}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path!r}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1

        # --- Task 1: Baseline Calculation (First 5 frames) ---
        baseline_energies = []
        for i in range(min(5, total_frames)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                baseline_energies.append(_dct_ac_energy(gray))
        
        baseline_dct = float(np.mean(baseline_energies)) if baseline_energies else 1.0
        # -----------------------------------------------------

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
            
            # Task 1: Normalize against baseline
            raw_dct = _dct_ac_energy(gray)
            dct_rel_score = (raw_dct - baseline_dct) / baseline_dct if baseline_dct > 0 else 0.0
            # If relative change is low, it's natural variation
            dct_suspicion = 0.0 if dct_rel_score < 0.15 else min(dct_rel_score, 1.0)
            dct_scores.append(dct_suspicion)
            
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
            delta_score = 1.0 - min(feat_delta_cv, 1.0)
        else:
            feat_delta_cv = 0.0
            delta_score = 0.0

        # LSB noise: natural variation is around 0.5. Only flag extreme proximity (< 0.005).
        lsb_suspicion = 1.0 - np.clip(abs(feat_lsb - 0.5) * 200.0, 0.0, 1.0)

        probability = float(np.clip(
            0.35 * lsb_suspicion +
            0.25 * feat_chi  +
            0.20 * feat_dct  +
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
                "lsb_noise":      round(lsb_suspicion, 4),
                "dct_ac_energy":  round(feat_dct, 4),
                "chi_square_lsb": round(feat_chi, 4),
                "frame_delta_cv": round(delta_score, 4),
            },
        }
