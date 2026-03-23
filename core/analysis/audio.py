"""
AudioAnalyzer — steganography detection for audio files.

Algorithm:
  1. MFCC variance check: compute MFCCs and examine their inter-frame
     variance.  LSB-encoded audio has unusually high MFCC variance in the
     higher coefficients.
  2. LSB noise ratio: fraction of samples whose LSB differs from the
     sign-magnitude prediction of their neighbours.
  3. Spectral flatness (Wiener entropy): unusually high flatness suggests
     noise-like modifications typical of LSB steganography.
  4. Weighted aggregate → probability in [0, 1].
"""

from __future__ import annotations

import os
from typing import Dict, Any

import numpy as np


# Optional imports — fallback gracefully if librosa/soundfile not available
try:
    import librosa
    _LIBROSA_OK = True
except (ImportError, TypeError):
    _LIBROSA_OK = False

try:
    import soundfile as sf
    _SF_OK = True
except (ImportError, TypeError):
    _SF_OK = False


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_audio(path: str):
    """Return (samples: np.ndarray[float32], sample_rate: int)."""
    if _LIBROSA_OK:
        try:
            y, sr = librosa.load(path, sr=None, mono=True)
            return y.astype(np.float32), int(sr)
        except (TypeError, Exception):
            # Fallback to soundfile if librosa fails at runtime (e.g. due to scipy/torch issues)
            pass
    if _SF_OK:
        try:
            y, sr = sf.read(path, dtype="float32", always_2d=False)
            if y.ndim > 1:
                y = y.mean(axis=1)
            return y, int(sr)
        except Exception:
            pass
    raise ImportError("Neither librosa nor soundfile could decode the audio.")


def _mfcc_variance_score(y: np.ndarray, sr: int) -> float:
    """
    High variance in upper MFCC coefficients is a sign of LSB manipulation.
    Returns a score in [0, 1].
    """
    if not _LIBROSA_OK:
        return 0.0

    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    # Focus on upper coefficients (indices 10–19) which are more sensitive
    upper = mfccs[10:, :]
    var_per_coeff = np.var(upper, axis=1)
    mean_var = float(var_per_coeff.mean())
    # Normalise: typical natural audio ~ 0–50; embedding pushes higher
    score = np.clip(mean_var / 100.0, 0.0, 1.0)
    return float(score)


def _lsb_noise_score(y: np.ndarray) -> float:
    """
    Quantise to 16-bit integers and compute LSB flip rate relative to
    neighbours.  Natural audio has correlated samples; embedding breaks
    that correlation in the LSB.
    Returns a score in [0, 1].
    """
    pcm = np.clip(y * 32767.0, -32768, 32767).astype(np.int16).astype(np.int32)
    lsb = pcm & 1
    # Horizontal neighbour prediction
    pred = np.roll(lsb, 1)
    pred[0] = lsb[0]
    flip_rate = float(np.abs(lsb - pred).mean())
    # Typical natural: ~0.45–0.50; steganographic: approaches 0.5 exactly
    # Score how close flip_rate is to 0.5 uniformity
    score = np.clip((flip_rate - 0.3) / 0.2, 0.0, 1.0)
    return float(score)


def _spectral_flatness_score(y: np.ndarray, sr: int) -> float:
    """
    Wiener entropy / spectral flatness.  Values close to 1 indicate
    noise-like content (possible embedding).
    Returns a score in [0, 1].
    """
    if _LIBROSA_OK:
        flatness = librosa.feature.spectral_flatness(y=y)
        mean_flat = float(flatness.mean())
    else:
        # Manual DFT-based flatness
        n_fft = 2048
        hop = n_fft // 2
        frames = [y[i:i+n_fft] for i in range(0, max(len(y) - n_fft, 1), hop)]
        flatness_vals = []
        for f in frames:
            mag = np.abs(np.fft.rfft(f * np.hanning(len(f))))
            mag = mag + 1e-12
            geometric = np.exp(np.log(mag).mean())
            arithmetic = mag.mean()
            flatness_vals.append(float(geometric / arithmetic))
        mean_flat = float(np.mean(flatness_vals)) if flatness_vals else 0.0

    # Higher flatness → more suspicious
    score = np.clip(mean_flat * 2.0, 0.0, 1.0)
    return float(score)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

class AudioAnalyzer:
    """Detect steganographic content hidden inside an audio file."""

    @classmethod
    def analyze(cls, audio_path: str) -> Dict[str, Any]:
        """
        Analyse *audio_path* for signs of steganographic embedding.

        Parameters
        ----------
        audio_path : str
            Path to the audio file (WAV, FLAC, MP3, …).

        Returns
        -------
        dict
            {
              "probability": float,   # 0.0 (clean) … 1.0 (likely stego)
              "verdict":     str,     # "CLEAN" | "SUSPICIOUS" | "LIKELY_STEGO"
              "features": {
                "mfcc_variance":     float,
                "lsb_noise":         float,
                "spectral_flatness": float,
              }
            }

        Raises
        ------
        ValueError
            If the file cannot be opened or decoded.
        """
        if not os.path.isfile(audio_path):
            raise ValueError(f"File not found: {audio_path!r}")

        try:
            y, sr = _load_audio(audio_path)
        except Exception as exc:
            raise ValueError(f"Cannot decode audio: {exc}") from exc

        if len(y) == 0:
            raise ValueError("Audio file contains no samples.")

        feat_mfcc  = _mfcc_variance_score(y, sr)
        feat_lsb   = _lsb_noise_score(y)
        feat_flat  = _spectral_flatness_score(y, sr)

        probability = float(np.clip(
            0.50 * feat_mfcc +
            0.25 * feat_lsb  +
            0.25 * feat_flat,
            0.0, 1.0
        ))

        if probability <= 0.20:
            verdict = "CLEAN"
        elif probability <= 0.55:
            verdict = "SUSPICIOUS"
        else:
            verdict = "LIKELY_STEGO"

        return {
            "probability": round(probability, 4),        # type: ignore[call-overload]
            "verdict": verdict,
            "features": {
                "mfcc_variance":     round(feat_mfcc, 4),  # type: ignore[call-overload]
                "lsb_noise":         round(feat_lsb, 4),   # type: ignore[call-overload]
                "spectral_flatness": round(feat_flat, 4),  # type: ignore[call-overload]
            },
        }
