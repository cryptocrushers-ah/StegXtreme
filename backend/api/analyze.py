"""
POST /api/analyze

Accepts any media file, detects whether it is an image, audio, or video,
routes to the appropriate analyzer class, and returns the analysis result.
"""

from __future__ import annotations

import os
import uuid
import urllib.parse
import shutil
import tempfile
from typing import Any, Dict
from fastapi import APIRouter, File, HTTPException, UploadFile

from core.analysis.image import ImageAnalyzer
from core.analysis.audio import AudioAnalyzer
from core.analysis.video import VideoAnalyzer
from core.analysis.threat import ThreatEngine
from backend.utils.validation import validate_file

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── MIME / extension routing ───────────────────────────────────────────────

_IMAGE_EXTS = {".png", ".bmp", ".tiff", ".tif", ".jpg", ".jpeg", ".webp"}
_AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".aac", ".m4a"}
_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}


def safe_file_path(file_path: str) -> str:
    """
    OpenCV on Windows cannot open files with spaces or special
    characters in the path. Copy to a safe temp path if needed.
    Returns the safe path — original file is never modified.
    """
    file_path = urllib.parse.unquote(file_path)
    file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    needs_copy = any(c in file_path for c in (" ", "(", ")", "[", "]", "&", "#", "'"))

    if needs_copy:
        ext = os.path.splitext(file_path)[1]
        tmp = tempfile.NamedTemporaryFile(
            suffix=ext, delete=False, dir=tempfile.gettempdir()
        )
        tmp.close()
        shutil.copy2(file_path, tmp.name)
        return tmp.name

    return file_path


def cleanup_temp(safe_path: str, original_path: str):
    """Delete temp file only if it was created by safe_file_path."""
    if safe_path != original_path and os.path.exists(safe_path):
        try:
            os.unlink(safe_path)
        except Exception:
            pass


def _detect_media_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _AUDIO_EXTS:
        return "audio"
    if ext in _VIDEO_EXTS:
        return "video"
    return "unknown"


# ── Endpoint ──────────────────────────────────────────────────────────────

@router.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    await validate_file(file)
    """
    Upload any media file (image, audio, video) and receive a
    steganography probability score with per-feature breakdown.

    Returns
    -------
    JSON with keys:
      - media_type : "image" | "audio" | "video"
      - probability : float  (0 = clean, 1 = very likely stego)
      - verdict     : "CLEAN" | "SUSPICIOUS" | "LIKELY_STEGO"
      - features    : dict of labeled feature scores
    """
    media_type = _detect_media_type(file.filename or "")
    if media_type == "unknown":
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type for '{file.filename}'. "
                f"Supported: PNG/BMP/TIFF/JPG (image), "
                f"WAV/FLAC (audio), MP4/AVI (video)."
            ),
        )

    # Save upload to temp with a safe UUID filename — no spaces
    ext      = os.path.splitext(file.filename or "file")[1]
    uid      = str(uuid.uuid4())
    in_path  = os.path.join(TEMP_DIR, f"{uid}_analyze{ext}")
    result: Dict[str, Any] = {}

    try:
        with open(in_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # in_path already has a safe UUID name — no need for safe_file_path
        if media_type == "image":
            result = ImageAnalyzer.analyze(in_path)
        elif media_type == "audio":
            result = AudioAnalyzer.analyze(in_path)
        else:
            result = VideoAnalyzer.analyze(in_path)

        result["media_type"] = media_type
        result["file_path"] = in_path  # Return the temp path for verification

        # Perform threat analysis using the unified ThreatEngine
        threat_report = ThreatEngine.analyze(in_path, result["probability"])
        result["threat"] = {
            "threat_level":         threat_report.threat_level,
            "threat_color":         threat_report.threat_color,
            "threat_score":         threat_report.threat_score,
            "primary_risk":         threat_report.primary_risk,
            "risks":                threat_report.risks,
            "recommendations":      threat_report.recommendations,
            "file_type_assessment": threat_report.file_type_assessment,
            "file_type_risk":       threat_report.file_type_risk,
            "strength_assessment":  threat_report.strength_assessment,
            "strength_risk":        threat_report.strength_risk,
            "safe_to_send":         threat_report.safe_to_send,
            "summary":              threat_report.summary
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    # File is NOT deleted here to allow the Verification engine to check it.
    # storage/temp is periodically cleaned by the system.

    return result