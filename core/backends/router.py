"""
router.py — Media-type router + per-type algorithm registry
===========================================================
Maps uploaded files to the correct backend and exposes which algorithms
are valid for each media type.  The frontend uses ALGORITHMS_FOR_TYPE
to build a dynamic algorithm selector.
"""

import mimetypes
from core.backends.image import ImageBackend
from core.backends.audio import AudioBackend
from core.backends.video import VideoBackend

mimetypes.init()

# ── Algorithm menus per media type ────────────────────────────────────
# Each entry: (value_sent_to_backend, human_label)
ALGORITHMS_FOR_TYPE: dict[str, list[dict]] = {
    "image": [
        {"value": "lsb",  "label": "LSB (Lossless, high capacity)"},
        {"value": "dct",  "label": "DCT (Robust to minor edits)"},
    ],
    "audio": [
        {"value": "lsb",  "label": "LSB (WAV only)"},
    ],
    "video": [
        {"value": "dwt_ss", "label": "DWT Spread-Spectrum (Recommended)"},
        {"value": "lsb",    "label": "LSB (Fast, lossless codec required)"},
    ],
}

# ── Accepted MIME types per category ─────────────────────────────────
_IMAGE_MIMES = {"image/png", "image/jpeg", "image/bmp", "image/tiff"}
_AUDIO_MIMES = {"audio/wav", "audio/x-wav", "audio/wave"}
_VIDEO_MIMES = {"video/mp4", "video/x-msvideo", "video/avi",
                "video/x-matroska", "video/quicktime"}

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
_AUDIO_EXTS = {".wav"}
_VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov"}


def _media_type(filepath: str) -> str:
    """Return 'image', 'audio', or 'video'. Raises ValueError if unknown."""
    mime, _ = mimetypes.guess_type(filepath)
    ext = "." + filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""

    if (mime in _IMAGE_MIMES) or (ext in _IMAGE_EXTS):
        return "image"
    if (mime in _AUDIO_MIMES) or (ext in _AUDIO_EXTS):
        return "audio"
    if (mime in _VIDEO_MIMES) or (ext in _VIDEO_EXTS):
        return "video"
    raise ValueError(f"Unsupported file type: mime={mime}, ext={ext}")


def get_backend(filepath: str):
    """Return the backend class for the given filepath."""
    t = _media_type(filepath)
    return {"image": ImageBackend, "audio": AudioBackend, "video": VideoBackend}[t]


def get_media_type(filepath: str) -> str:
    """Public wrapper used by API endpoints."""
    return _media_type(filepath)
