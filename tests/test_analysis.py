"""
tests/test_analysis.py

Unit tests for the three analysis modules:
  - core.analysis.image.ImageAnalyzer
  - core.analysis.audio.AudioAnalyzer
  - core.analysis.video.VideoAnalyzer

All tests are self-contained and use synthetic in-memory data so that no
external files need to be present.  PIL, NumPy, SoundFile, and OpenCV are
required (they are already in requirements.txt).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import wave

import numpy as np
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analysis.image import ImageAnalyzer
from core.analysis.audio import AudioAnalyzer
from core.analysis.video import VideoAnalyzer


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures / helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_png(mode: str = "natural") -> str:
    """Write a temporary PNG and return the file path."""
    from PIL import Image, ImageFilter

    rng = np.random.default_rng(42)
    if mode == "natural":
        # Gaussian-blurred noise: non-uniform pixels distribution with
        # LSBs correlated to neighbours → low chi-square suspicious score.
        base = rng.normal(128, 40, (256, 256, 3)).clip(0, 255).astype(np.uint8)
        img_tmp = Image.fromarray(base, "RGB").filter(ImageFilter.GaussianBlur(radius=4))
        arr = np.array(img_tmp, dtype=np.uint8)
        # Force even LSBs to remove randomness from LSB plane
        arr = (arr & 0xFE)  # clear all LSBs
    elif mode == "stego":
        # Fully random pixels with alternating LSBs – maximum uniform LSB distribution
        arr = rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)
        # Build a (256, 256) alternating 0/1 mask and broadcast to 3 channels
        row_idx = np.arange(256).reshape(-1, 1)
        col_idx = np.arange(256).reshape(1, -1)
        lsb_2d = ((row_idx + col_idx) % 2).astype(np.uint8)      # shape (256,256)
        lsb_mask = np.stack([lsb_2d, lsb_2d, lsb_2d], axis=2)   # shape (256,256,3)
        arr = (arr & 0xFE) | lsb_mask
    else:
        arr = np.zeros((64, 64, 3), dtype=np.uint8)

    img = Image.fromarray(arr, "RGB")
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    tmp.close()
    return tmp.name


def _make_wav(mode: str = "natural") -> str:
    """Write a temporary WAV and return the file path."""
    sr = 22050
    duration = 1.0
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    if mode == "natural":
        # Simple sine wave
        samples = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    else:
        # Random noise – high spectral flatness
        rng = np.random.default_rng(0)
        samples = rng.integers(-32768, 32767, n, dtype=np.int16)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    tmp.close()
    return tmp.name


def _make_video() -> str:
    """Write a minimal MP4-like AVI using OpenCV and return the file path."""
    import cv2

    tmp = tempfile.NamedTemporaryFile(suffix=".avi", delete=False)
    tmp.close()

    out = cv2.VideoWriter(
        tmp.name,
        cv2.VideoWriter_fourcc(*"MJPG"),
        10,
        (64, 64),
    )
    rng = np.random.default_rng(7)
    for _ in range(20):
        frame = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    return tmp.name


# ──────────────────────────────────────────────────────────────────────────────
# ImageAnalyzer tests
# ──────────────────────────────────────────────────────────────────────────────

class TestImageAnalyzer:

    def test_returns_required_keys(self):
        path = _make_png("natural")
        try:
            result = ImageAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert "probability" in result
        assert "verdict" in result
        assert "features" in result

    def test_probability_range(self):
        path = _make_png("natural")
        try:
            result = ImageAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert 0.0 <= result["probability"] <= 1.0

    def test_verdict_is_valid(self):
        path = _make_png("natural")
        try:
            result = ImageAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert result["verdict"] in {"CLEAN", "SUSPICIOUS", "LIKELY_STEGO"}

    def test_features_dict_non_empty(self):
        path = _make_png("natural")
        try:
            result = ImageAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert len(result["features"]) > 0
        for v in result["features"].values():
            assert 0.0 <= v <= 1.0

    def test_nonexistent_file_raises(self):
        with pytest.raises(ValueError, match="File not found"):
            ImageAnalyzer.analyze("/nonexistent/path/image.png")

    def test_natural_image_lower_probability_than_random(self):
        nat_path  = _make_png("natural")
        steg_path = _make_png("stego")
        try:
            nat_result  = ImageAnalyzer.analyze(nat_path)
            steg_result = ImageAnalyzer.analyze(steg_path)
        finally:
            os.unlink(nat_path)
            os.unlink(steg_path)

        # Random (stego-like) pixels should score higher than a smooth gradient
        assert nat_result["probability"] <= steg_result["probability"]


# ──────────────────────────────────────────────────────────────────────────────
# AudioAnalyzer tests
# ──────────────────────────────────────────────────────────────────────────────

class TestAudioAnalyzer:

    def test_returns_required_keys(self):
        path = _make_wav("natural")
        try:
            result = AudioAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert "probability" in result
        assert "verdict"     in result
        assert "features"    in result

    def test_probability_range(self):
        path = _make_wav("natural")
        try:
            result = AudioAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert 0.0 <= result["probability"] <= 1.0

    def test_verdict_is_valid(self):
        path = _make_wav("natural")
        try:
            result = AudioAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert result["verdict"] in {"CLEAN", "SUSPICIOUS", "LIKELY_STEGO"}

    def test_features_in_range(self):
        path = _make_wav("natural")
        try:
            result = AudioAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        for v in result["features"].values():
            assert 0.0 <= v <= 1.0

    def test_nonexistent_file_raises(self):
        with pytest.raises(ValueError, match="File not found"):
            AudioAnalyzer.analyze("/nonexistent/audio.wav")


# ──────────────────────────────────────────────────────────────────────────────
# VideoAnalyzer tests
# ──────────────────────────────────────────────────────────────────────────────

class TestVideoAnalyzer:

    def test_returns_required_keys(self):
        path = _make_video()
        try:
            result = VideoAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert "probability" in result
        assert "verdict"     in result
        assert "features"    in result

    def test_probability_range(self):
        path = _make_video()
        try:
            result = VideoAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert 0.0 <= result["probability"] <= 1.0

    def test_verdict_is_valid(self):
        path = _make_video()
        try:
            result = VideoAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        assert result["verdict"] in {"CLEAN", "SUSPICIOUS", "LIKELY_STEGO"}

    def test_feature_keys_present(self):
        path = _make_video()
        try:
            result = VideoAnalyzer.analyze(path)
        finally:
            os.unlink(path)

        required = {"lsb_noise", "dct_ac_energy", "chi_square_lsb", "frame_delta_cv"}
        assert required.issubset(result["features"].keys())

    def test_nonexistent_file_raises(self):
        with pytest.raises(ValueError, match="File not found"):
            VideoAnalyzer.analyze("/nonexistent/video.mp4")
