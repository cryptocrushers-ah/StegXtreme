import pytest
from fastapi.testclient import TestClient
import sys
from unittest.mock import MagicMock

# Mock torch before it's imported by other modules
mock_torch = MagicMock()
mock_torch.__path__ = []
sys.modules["torch"] = mock_torch
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.optim"] = MagicMock()

from backend.main import app

client = TestClient(app)

def test_health_check_unauthenticated():
    # Health check should be public
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_success():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

def test_protected_route_unauthenticated():
    # Attempt to access a protected route without a token
    response = client.post("/api/tunnel/send", json={
        "protocol": "http",
        "payload": "test",
        "target": "http://test.com",
        "session_id": "test"
    })
    assert response.status_code == 401

def test_protected_route_authenticated():
    # Get token
    login_response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    
    # Access protected route
    response = client.post(
        "/api/tunnel/send",
        json={
            "protocol": "http",
            "payload": "test",
            "target": "http://test.com",
            "session_id": "test"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    # The route might fail for other reasons (like real networking), 
    # but it shouldn't be a 401.
    assert response.status_code != 401
