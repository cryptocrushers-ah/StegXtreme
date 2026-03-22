import pytest
import os
from fastapi.testclient import TestClient
from backend.main import app
from core.analysis.threat import ThreatEngine

client = TestClient(app)

from backend.api.auth import get_current_user
from unittest.mock import patch, MagicMock

# Global mock for auth in tests
app.dependency_overrides[get_current_user] = lambda: {"uid": "test_user"}

@pytest.fixture
def mock_file_utils():
    with patch("os.path.getsize", return_value=100 * 1024), \
         patch("cv2.imread", return_value=MagicMock()), \
         patch("cv2.Laplacian") as mock_laplacian:
        mock_laplacian.return_value.var.return_value = 600
        yield

def test_safe_threat_level(mock_file_utils):
    report = ThreatEngine.analyze("test.png", 0.10)
    assert report.threat_level == "SAFE"
    assert report.safe_to_send is True

def test_critical_threat_level(mock_file_utils):
    report = ThreatEngine.analyze("test.png", 0.90)
    assert report.threat_level == "CRITICAL"
    assert report.safe_to_send is False

def test_jpeg_file_high_risk(mock_file_utils):
    report = ThreatEngine.analyze("test.jpg", 0.30)
    assert report.file_type_risk == "HIGH"

def test_png_file_low_risk(mock_file_utils):
    report = ThreatEngine.analyze("test.png", 0.30)
    assert report.file_type_risk == "LOW"

def test_high_strength_risk(mock_file_utils):
    report = ThreatEngine.analyze("test.png", 0.30, embed_strength=30)
    assert report.strength_risk == "HIGH"

def test_low_strength_ok(mock_file_utils):
    report = ThreatEngine.analyze("test.png", 0.30, embed_strength=14)
    assert report.strength_risk == "LOW"

def test_recommendations_not_empty(mock_file_utils):
    report = ThreatEngine.analyze("test.jpg", 0.60)
    assert len(report.recommendations) > 0

def test_threat_endpoint_returns_200(mock_file_utils):
    response = client.post(
        "/api/analyze/threat",
        json={
            "file_path": "test.png",
            "detection_prob": 0.73,
            "embed_strength": 18.0
        }
    )
    assert response.status_code == 200
    assert response.json()["threat_level"] == "HIGH"

def test_threat_endpoint_missing_prob():
    response = client.post(
        "/api/analyze/threat",
        json={"file_path": "test.png"},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
