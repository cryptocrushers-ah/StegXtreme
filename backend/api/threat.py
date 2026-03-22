from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.analysis.threat import ThreatEngine

router = APIRouter()

class ThreatRequest(BaseModel):
    file_path: str
    detection_prob: float
    embed_strength: Optional[float] = None

class ThreatResponse(BaseModel):
    threat_level: str
    threat_color: str
    threat_score: float
    primary_risk: str
    risks: List[str]
    recommendations: List[str]
    file_type_assessment: str
    file_type_risk: str
    strength_assessment: str
    strength_risk: str
    safe_to_send: bool
    summary: str

@router.post("/api/analyze/threat", response_model=ThreatResponse)
async def analyze_threat(request: ThreatRequest):
    try:
        report = ThreatEngine.analyze(
            request.file_path,
            request.detection_prob,
            request.embed_strength
        )
        return ThreatResponse(
            threat_level=report.threat_level,
            threat_color=report.threat_color,
            threat_score=report.threat_score,
            primary_risk=report.primary_risk,
            risks=report.risks,
            recommendations=report.recommendations,
            file_type_assessment=report.file_type_assessment,
            file_type_risk=report.file_type_risk,
            strength_assessment=report.strength_assessment,
            strength_risk=report.strength_risk,
            safe_to_send=report.safe_to_send,
            summary=report.summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
