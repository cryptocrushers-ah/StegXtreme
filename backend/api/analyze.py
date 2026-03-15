"""
POST /api/analyze

Accepts any media file, detects whether it is an image, audio, or video,
routes to the appropriate analyzer class, and returns the analysis result.
"""

from __future__ import annotations

import os
import shutil
import uuid
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from core.analysis.image import ImageAnalyzer
from core.analysis.audio import AudioAnalyzer
from core.analysis.video import VideoAnalyzer

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── MIME / extension routing ──────────────────────────────────────────────────

_IMAGE_EXTS = {".png", ".bmp", ".tiff", ".tif", ".jpg", ".jpeg", ".webp"}
_AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".aac", ".m4a"}
_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}


def _detect_media_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _AUDIO_EXTS:
        return "audio"
    if ext in _VIDEO_EXTS:
        return "video"
    return "unknown"


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload any media file (image, audio, video) and receive a steganography
    probability score together with per-feature breakdown.

    Returns
    -------
    JSON with keys:
      - media_type : "image" | "audio" | "video"
      - probability : float   (0 = clean, 1 = very likely stego)
      - verdict     : "CLEAN" | "SUSPICIOUS" | "LIKELY_STEGO"
      - features    : dict of labeled feature scores
    """
    media_type = _detect_media_type(file.filename or "")
    if media_type == "unknown":
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type for '{file.filename}'. "
                   f"Supported: PNG/BMP/TIFF (image), WAV/FLAC (audio), MP4/AVI (video).",
        )

    # Save to temp
    ext = os.path.splitext(file.filename or "file")[1]
    uid = str(uuid.uuid4())
    in_path = os.path.join(TEMP_DIR, f"{uid}_analyze{ext}")
    result: Dict[str, Any] = {}

    try:
        with open(in_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        if media_type == "image":
            result = ImageAnalyzer.analyze(in_path)
        elif media_type == "audio":
            result = AudioAnalyzer.analyze(in_path)
        else:
            result = VideoAnalyzer.analyze(in_path)

        result["media_type"] = media_type

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        # Clean up temp file
        if in_path and os.path.exists(in_path):
            try:
                os.remove(in_path)
            except OSError:
                pass

    return result
