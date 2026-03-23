import os
import urllib.parse
import shutil
import tempfile
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.analysis.threat import ThreatEngine

router = APIRouter()


# ── Safe File Path Helper ─────────────────────────────────────────────────

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
    """Delete temp file only if it was created by safe_file_path."""
    if safe_path != original_path and os.path.exists(safe_path):
        try:
            os.unlink(safe_path)
        except Exception:
            pass


# ── Models ────────────────────────────────────────────────────────────────

class ThreatRequest(BaseModel):
    file_path      : str
    detection_prob : float
    embed_strength : Optional[float] = None


class ThreatResponse(BaseModel):
    threat_level         : str
    threat_color         : str
    threat_score         : float
    primary_risk         : str
    risks                : List[str]
    recommendations      : List[str]
    file_type_assessment : str
    file_type_risk       : str
    strength_assessment  : str
    strength_risk        : str
    safe_to_send         : bool
    summary              : str


# ── Endpoint ──────────────────────────────────────────────────────────────

@router.post("/api/analyze/threat", response_model=ThreatResponse)
async def analyze_threat(request: ThreatRequest):
    """
    Analyze threat level of an embedded file.
    Returns structured threat report with risks and recommendations.
    """
    original  = urllib.parse.unquote(request.file_path)
    safe_path = None

    try:
        # handle files with spaces or special chars in path
        safe_path = safe_file_path(request.file_path)

        report = ThreatEngine.analyze(
            safe_path,
            request.detection_prob,
            request.embed_strength
        )

        return ThreatResponse(
            threat_level         = report.threat_level,
            threat_color         = report.threat_color,
            threat_score         = report.threat_score,
            primary_risk         = report.primary_risk,
            risks                = report.risks,
            recommendations      = report.recommendations,
            file_type_assessment = report.file_type_assessment,
            file_type_risk       = report.file_type_risk,
            strength_assessment  = report.strength_assessment,
            strength_risk        = report.strength_risk,
            safe_to_send         = report.safe_to_send,
            summary              = report.summary
        )

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Threat analysis failed: {str(exc)}"
        )
    finally:
        # clean up temp file if one was created
        if safe_path:
            cleanup_temp(safe_path, os.path.abspath(
                urllib.parse.unquote(request.file_path)
            ))