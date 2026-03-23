"""
ImageAnalyzer — steganography detection for image files.
GPU-accelerated via CuPy when available.
Falls back to CPU (NumPy) transparently.
"""

from __future__ import annotations

import os
import math
from typing import Dict, Any

import numpy as np
from PIL import Image
from scipy.stats import chi2 as chi2_dist

# ── GPU setup — mirrors core/compute/backend.py pattern ──────────────────
try:
    import cupy as cp
    from core.compute.backend import GPU_ENABLED
    _USE_GPU = GPU_ENABLED
except Exception:
    cp         = None       # type: ignore
    _USE_GPU   = False


# ══════════════════════════════════════════════════════════════════════════
# GPU helpers
# ══════════════════════════════════════════════════════════════════════════

def _gpu_chi_square(ch_gpu) -> float:
    """Chi-square on a single GPU channel array."""
    hist   = cp.bincount(ch_gpu.ravel(), minlength=256).astype(cp.float64)
    pairs  = hist.reshape(-1, 2)
    exp    = pairs.sum(axis=1, keepdims=True) / 2.0
    chi2_v = float(
        cp.where(exp > 1.0, (pairs - exp) ** 2 / exp, 0.0)
        .sum().get()
    )
    dof   = len(pairs) - 1
    p_val = float(chi2_dist.sf(chi2_v, dof))
    return float(np.clip((p_val - 0.995) / 0.005, 0.0, 1.0))


def _gpu_lsb_entropy(gray_gpu) -> float:
    """Shannon entropy of LSB plane on GPU."""
    lsb = (gray_gpu & 1).astype(cp.float32)
    p1  = float(lsb.mean().get())
    p0  = 1.0 - p1
    eps = 1e-12
    ent = -(p1 * math.log2(p1 + eps) + p0 * math.log2(p0 + eps))
    return float(np.clip((ent - 0.999) / 0.001, 0.0, 1.0))


def _gpu_sample_pairs(gray_gpu) -> float:
    """LSB uniformity score on GPU."""
    lsb = (gray_gpu & 1).astype(cp.float32)
    p1  = float(lsb.mean().get())
    dev = abs(p1 - 0.5)
    return float(1.0 - np.clip(dev * 80.0, 0.0, 1.0))


# ══════════════════════════════════════════════════════════════════════════
# CPU helpers — original implementations kept as fallback
# ══════════════════════════════════════════════════════════════════════════

def _cpu_chi_square_score(channel: np.ndarray) -> float:
    hist     = np.bincount(channel.ravel(), minlength=256).astype(np.float64)
    pairs    = hist.reshape(-1, 2)
    expected = pairs.sum(axis=1, keepdims=True) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2_val = np.where(
            expected > 1.0,
            (pairs - expected) ** 2 / expected,
            0.0
        ).sum()
    dof   = len(pairs) - 1
    p_val = float(chi2_dist.sf(chi2_val, dof))
    return float(np.clip((p_val - 0.995) / 0.005, 0.0, 1.0))


def _cpu_sample_pairs_score(channel: np.ndarray) -> float:
    lsb   = channel & 1
    ratio = float(lsb.mean())
    dev   = abs(ratio - 0.5)
    return float(1.0 - np.clip(dev * 80.0, 0.0, 1.0))


def _cpu_lsb_entropy(channel: np.ndarray) -> float:
    lsb     = channel & 1
    p1      = float(lsb.mean())
    p0      = 1.0 - p1
    eps     = 1e-12
    entropy = -(p1 * np.log2(p1 + eps) + p0 * np.log2(p0 + eps))
    return float(np.clip((entropy - 0.999) / 0.001, 0.0, 1.0))


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════

class ImageAnalyzer:
    """
    Detect steganographic content inside an image file.
    Uses GPU (CuPy) when available — falls back to CPU transparently.
    """

    @classmethod
    def analyze(cls, image_path: str) -> Dict[str, Any]:
        if not os.path.isfile(image_path):
            raise ValueError(f"File not found: {image_path!r}")

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Cannot open image: {exc}") from exc

        arr  = np.array(img, dtype=np.uint8)
        mode = "GPU" if _USE_GPU else "CPU"

        chi_r = chi_g = chi_b = sp_score = lsb_ent = 0.0

        if _USE_GPU:
            try:
                # Upload entire image to GPU once — no repeated transfers
                arr_gpu  = cp.asarray(arr)
                r_gpu    = arr_gpu[:, :, 0]
                g_gpu    = arr_gpu[:, :, 1]
                b_gpu    = arr_gpu[:, :, 2]
                gray_gpu = (
                    0.299 * r_gpu.astype(cp.float32) +
                    0.587 * g_gpu.astype(cp.float32) +
                    0.114 * b_gpu.astype(cp.float32)
                ).astype(cp.uint8)

                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=5) as ex:
                    f_chi_r = ex.submit(_gpu_chi_square,   r_gpu)
                    f_chi_g = ex.submit(_gpu_chi_square,   g_gpu)
                    f_chi_b = ex.submit(_gpu_chi_square,   b_gpu)
                    f_sp    = ex.submit(_gpu_sample_pairs, gray_gpu)
                    f_lsb   = ex.submit(_gpu_lsb_entropy,  gray_gpu)
                    chi_r   = f_chi_r.result()
                    chi_g   = f_chi_g.result()
                    chi_b   = f_chi_b.result()
                    sp_score = f_sp.result()
                    lsb_ent  = f_lsb.result()

                del arr_gpu, r_gpu, g_gpu, b_gpu, gray_gpu
                cp.get_default_memory_pool().free_all_blocks()

            except Exception:
                mode = "CPU (GPU fallback)"
                chi_r, chi_g, chi_b, sp_score, lsb_ent = \
                    cls._cpu_features(arr)
        else:
            chi_r, chi_g, chi_b, sp_score, lsb_ent = \
                cls._cpu_features(arr)

        chi_mean    = (chi_r + chi_g + chi_b) / 3.0
        probability = float(np.clip(
            0.80 * chi_mean +
            0.10 * sp_score +
            0.10 * lsb_ent,
            0.0, 1.0
        ))

        verdict = (
            "CLEAN"       if probability <= 0.20 else
            "SUSPICIOUS"  if probability <= 0.55 else
            "LIKELY_STEGO"
        )

        return {
            "probability": round(probability, 4),
            "verdict":     verdict,
            "features": {
                "chi_square_r": round(chi_r,     4),
                "chi_square_g": round(chi_g,     4),
                "chi_square_b": round(chi_b,     4),
                "sample_pairs": round(sp_score,  4),
                "lsb_entropy":  round(lsb_ent,   4),
            },
            "compute_mode": mode,
        }

    @staticmethod
    def _cpu_features(arr: np.ndarray):
        r, g, b  = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        gray_arr = np.array(
            Image.fromarray(arr).convert("L"), dtype=np.uint8
        )
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            f_chi_r = executor.submit(_cpu_chi_square_score,  r)
            f_chi_g = executor.submit(_cpu_chi_square_score,  g)
            f_chi_b = executor.submit(_cpu_chi_square_score,  b)
            f_sp    = executor.submit(_cpu_sample_pairs_score, gray_arr)
            f_lsb   = executor.submit(_cpu_lsb_entropy,       gray_arr)
            return (
                f_chi_r.result(), f_chi_g.result(), f_chi_b.result(),
                f_sp.result(),    f_lsb.result()
            )