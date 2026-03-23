from dataclasses import dataclass, field
import os
import cv2
import numpy as np
from typing import List, Optional, Tuple
import urllib.parse

@dataclass
class ThreatReport:
    threat_level: str
    threat_color: str
    threat_score: float
    primary_risk: str
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    file_type_assessment: str = ""
    file_type_risk: str = ""
    strength_assessment: str = ""
    strength_risk: str = ""
    safe_to_send: bool = False
    summary: str = ""

class ThreatEngine:
    THRESHOLDS = [
        (0.20, "SAFE", "#22C55E", True),
        (0.35, "LOW", "#84CC16", True),
        (0.55, "MODERATE", "#EAB308", True), # Specs say "With caution" but safe_to_send is bool, I'll use True as it's not explicitly No. Wait, specs say "With caution" for SAFE TO SEND. Actually, let's look at the table again.
        # SAFE: Yes, LOW: Yes, MODERATE: With caution, HIGH: No, CRITICAL: No.
        # I'll treat MODERATE as safe_to_send=True for simplicity, or False if we want to be strict.
        # Actually, let's use the exact rules.
        (0.75, "HIGH", "#F97316", False),
        (1.00, "CRITICAL", "#EF4444", False)
    ]

    @staticmethod
    def analyze(file_path: str, detection_prob: float, embed_strength: Optional[float] = None) -> ThreatReport:
        # Determine threat level and color
        threat_level = "SAFE"
        threat_color = "#22C55E"
        safe_to_send = True
        
        if detection_prob <= 0.20:
            threat_level, threat_color, safe_to_send = "SAFE", "#22C55E", True
        elif detection_prob <= 0.35:
            threat_level, threat_color, safe_to_send = "LOW", "#84CC16", True
        elif detection_prob <= 0.55:
            threat_level, threat_color, safe_to_send = "MODERATE", "#EAB308", True
        elif detection_prob <= 0.75:
            threat_level, threat_color, safe_to_send = "HIGH", "#F97316", False
        else:
            threat_level, threat_color, safe_to_send = "CRITICAL", "#EF4444", False

        risks = []
        
        # File type check
        ft_assessment, ft_risk = ThreatEngine._check_file_type_risk(file_path)
        if ft_risk in ["MEDIUM", "HIGH"]:
            risks.append(f"{os.path.splitext(file_path)[1].upper()} format")

        # Strength check
        s_assessment, s_risk = "", ""
        if embed_strength is not None:
            s_assessment, s_risk = ThreatEngine._check_strength_risk(embed_strength)
            if s_risk in ["MEDIUM", "HIGH"]:
                risks.append("High embed strength")

        # Texture check (images only)
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            t_assessment, t_risk = ThreatEngine._check_texture_risk(file_path)
            if t_risk in ["MEDIUM", "HIGH"]:
                risks.append("Low texture region")

        # Size check
        sz_assessment, sz_risk = ThreatEngine._check_size_risk(file_path)
        if sz_risk in ["MEDIUM", "HIGH"]:
            risks.append("Small file size")

        # Primary risk
        primary_risk = "No significant risks detected"
        if risks:
            # Map specific primary risks based on priority
            if ".JPG" in [r.upper() for r in risks]:
                primary_risk = "JPEG compression will degrade your payload"
            elif "High embed strength" in risks:
                primary_risk = "Embed strength is too aggressive for this carrier"
            elif "Low texture region" in risks:
                primary_risk = "LSB patterns in smooth regions are detectable"
            else:
                primary_risk = risks[0]

        recommendations = ThreatEngine._generate_recommendations(risks, file_path, embed_strength, threat_level)

        summary = f"One sentence plain English verdict: {threat_level} detection risk — "
        if safe_to_send:
            summary += "this file is likely safe to send."
        else:
            summary += "switch file format or reduce strength before sending."

        return ThreatReport(
            threat_level=threat_level,
            threat_color=threat_color,
            threat_score=detection_prob,
            primary_risk=primary_risk,
            risks=risks,
            recommendations=recommendations,
            file_type_assessment=ft_assessment,
            file_type_risk=ft_risk,
            strength_assessment=s_assessment,
            strength_risk=s_risk,
            safe_to_send=safe_to_send,
            summary=summary
        )

    @staticmethod
    def _check_file_type_risk(file_path: str) -> Tuple[str, str]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            return "JPEG compression degrades payload — bits may be lost on save", "HIGH"
        if ext == ".png":
            return "PNG is lossless — perfect format for steganography", "LOW"
        if ext in [".mp4", ".avi"]:
            return "Video compression varies by codec — H.264 is safer than H.265", "MEDIUM"
        if ext == ".wav":
            return "WAV is uncompressed audio — excellent carrier format", "LOW"
        if ext == ".mp3":
            return "MP3 compression destroys LSB data — avoid for embedding", "HIGH"
        return "Unknown format — verify it is lossless before use", "MEDIUM"

    @staticmethod
    def _check_strength_risk(embed_strength: float) -> Tuple[str, str]:
        if embed_strength < 10:
            return "Subtle embed, hard to detect", "LOW"
        if embed_strength <= 18:
            return "Balanced, recommended range", "LOW"
        if embed_strength <= 25:
            return "Noticeable to neural detectors", "MEDIUM"
        return "Too aggressive, clearly visible to analysis", "HIGH"

    @staticmethod
    def _check_texture_risk(file_path: str) -> Tuple[str, str]:
        file_path = urllib.parse.unquote(file_path)
        file_path = os.path.abspath(file_path)
        try:
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return "Could not analyze texture", "MEDIUM"
            variance = cv2.Laplacian(img, cv2.CV_64F).var()
            if variance < 100:
                return f"Uniform regions (variance {variance:.1f}) — high risk", "HIGH"
            if variance <= 500:
                return f"Moderate texture (variance {variance:.1f})", "MEDIUM"
            return f"Complex texture (variance {variance:.1f})", "LOW"
        except Exception:
            return "Texture analysis failed", "MEDIUM"

    @staticmethod
    def _check_size_risk(file_path: str) -> Tuple[str, str]:
        size_kb = os.path.getsize(file_path) / 1024
        if size_kb < 50:
            return "Too small, embed distorts significant portion of data", "HIGH"
        if size_kb <= 200:
            return "Acceptable but limited capacity", "MEDIUM"
        return "Plenty of carrier data to hide in", "LOW"

    @staticmethod
    def _generate_recommendations(risks: List[str], file_path: str, embed_strength: Optional[float], threat_level: str) -> List[str]:
        recs = []
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in [".jpg", ".jpeg"]:
            recs.append("Switch to PNG — lossless format preserves every bit of your hidden payload")
        if ext == ".mp3":
            recs.append("Switch to WAV format — MP3 compression destroys hidden data")
        
        if embed_strength and embed_strength > 25:
            recs.append(f"Reduce embed strength from {embed_strength} to 14 — less detectable while still reliable")
        elif not embed_strength:
            recs.append("Check your embed settings and re-analyze after embedding")

        if any("texture" in r.lower() for r in risks):
            recs.append("Choose images with high texture — urban scenes, foliage, and crowds are ideal")
        
        if any("size" in r.lower() for r in risks):
            recs.append("Use larger carrier files — minimum 200KB recommended for safe embedding")

        if threat_level == "HIGH":
            recs.append("Do not send this file — start fresh with a different carrier image")
        elif threat_level == "CRITICAL":
            recs.append("This embed is almost certainly detectable — discard and re-embed")
            
        return recs[:4] # Up to 4 recommendations
