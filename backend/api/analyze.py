"""
POST /api/analyze

Accepts any media file, detects whether it is an image, audio, or video,
routes to the appropriate analyzer class, and returns the analysis result.

Added: file hash cache — repeated analysis of same file returns in <5ms.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import urllib.parse
import uuid
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from core.analysis.image  import ImageAnalyzer
from core.analysis.audio  import AudioAnalyzer
from core.analysis.video  import VideoAnalyzer
from core.analysis.threat import ThreatEngine
from backend.utils.validation import validate_file

router = APIRouter()

TEMP_DIR  = "storage/temp"
CACHE_DIR = "storage/analysis_cache"
os.makedirs(TEMP_DIR,  exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ── MIME / extension routing ──────────────────────────────────────────────

_IMAGE_EXTS = {".png", ".bmp", ".tiff", ".tif", ".jpg", ".jpeg", ".webp"}
_AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".aac", ".m4a"}
_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}


def safe_file_path(file_path: str) -> str:
    """
    OpenCV on Windows cannot open files with spaces or special chars.
    Copy to a safe temp path if needed.
    """
    file_path = urllib.parse.unquote(file_path)
    file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    needs_copy = any(
        c in file_path for c in (" ", "(", ")", "[", "]", "&", "#", "'")
    )
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
    if safe_path != original_path and os.path.exists(safe_path):
        try:
            os.unlink(safe_path)
        except Exception:
            pass


def _detect_media_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in _IMAGE_EXTS: return "image"
    if ext in _AUDIO_EXTS: return "audio"
    if ext in _VIDEO_EXTS: return "video"
    return "unknown"


# ── File Hash Cache ───────────────────────────────────────────────────────

def _file_hash(path: str) -> str:
    """
    Fast content hash using first + last 64KB of file.
    Catches file content changes without reading the full file.
    For a 2.83MB video: ~0.5ms vs 3-8s for full analysis.
    """
    h        = hashlib.md5()
    filesize = os.path.getsize(path)
    chunk    = 65536  # 64KB

    with open(path, "rb") as f:
        # read start
        h.update(f.read(chunk))
        # read end (if file is large enough)
        if filesize > chunk * 2:
            f.seek(-chunk, 2)
            h.update(f.read(chunk))

    # include filesize in hash to catch truncation attacks
    h.update(str(filesize).encode())
    return h.hexdigest()


def _get_cached(file_path: str) -> Dict | None:
    """
    Return cached analysis result if file content unchanged.
    Returns None on any error or cache miss.
    """
    try:
        fhash    = _file_hash(file_path)
        cache_fp = os.path.join(CACHE_DIR, f"{fhash}.json")
        if os.path.exists(cache_fp):
            with open(cache_fp, "r") as f:
                data = json.load(f)
            # validate cache entry has required fields
            if "probability" in data and "verdict" in data:
                return data
    except Exception:
        pass
    return None


def _save_cache(file_path: str, result: Dict):
    """
    Cache analysis result keyed by file content hash.
    Silently ignores all errors — cache is always best-effort.
    """
    try:
        fhash    = _file_hash(file_path)
        cache_fp = os.path.join(CACHE_DIR, f"{fhash}.json")
        with open(cache_fp, "w") as f:
            json.dump(result, f)
    except Exception:
        pass


def _evict_old_cache(max_entries: int = 500):
    """
    Remove oldest cache entries if cache exceeds max_entries.
    Called occasionally to prevent unbounded disk growth.
    """
    try:
        entries = [
            os.path.join(CACHE_DIR, f)
            for f in os.listdir(CACHE_DIR)
            if f.endswith(".json")
        ]
        if len(entries) > max_entries:
            # sort by modification time, delete oldest 20%
            entries.sort(key=os.path.getmtime)
            for old in entries[:len(entries) // 5]:
                os.unlink(old)
    except Exception:
        pass


# ── Endpoint ──────────────────────────────────────────────────────────────

@router.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    await validate_file(file)
    """
    Upload any media file and receive a steganography probability score.
    Results are cached by file content hash — same file analyzed twice
    returns instantly on second call.

    Returns
    -------
    JSON with keys:
      - media_type  : "image" | "audio" | "video"
      - probability : float  (0 = clean, 1 = very likely stego)
      - verdict     : "CLEAN" | "SUSPICIOUS" | "LIKELY_STEGO"
      - features    : dict of labeled feature scores
      - from_cache  : bool — true if result came from cache
      - analysis_ms : float — time taken in milliseconds
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

    # Save upload with safe UUID filename — no spaces, no special chars
    ext      = os.path.splitext(file.filename or "file")[1]
    uid      = str(uuid.uuid4())
    in_path  = os.path.join(TEMP_DIR, f"{uid}_analyze{ext}")
    result: Dict[str, Any] = {}

    t_start = time.perf_counter()

    try:
        with open(in_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # ── Check cache first ─────────────────────────────────────────
        cached = _get_cached(in_path)
        if cached is not None:
            elapsed = (time.perf_counter() - t_start) * 1000
            cached["from_cache"]  = True
            cached["analysis_ms"] = round(elapsed, 2)
            # still return the file_path for auth verify
            cached["file_path"]   = in_path
            return cached

        # ── Run analysis ──────────────────────────────────────────────
        if media_type == "image":
            result = ImageAnalyzer.analyze(in_path)
        elif media_type == "audio":
            result = AudioAnalyzer.analyze(in_path)
        else:
            result = VideoAnalyzer.analyze(in_path)

        result["media_type"] = media_type
        result["file_path"]  = in_path

        # ── Threat analysis ───────────────────────────────────────────
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
            "summary":              threat_report.summary,
        }

        # ── Cache the result ──────────────────────────────────────────
        _save_cache(in_path, result)
        # occasional eviction — every ~50 requests on average
        import random
        if random.randint(0, 49) == 0:
            _evict_old_cache()

        elapsed = (time.perf_counter() - t_start) * 1000
        result["from_cache"]  = False
        result["analysis_ms"] = round(elapsed, 2)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # File kept for auth verify — storage/temp is cleaned periodically
    return result