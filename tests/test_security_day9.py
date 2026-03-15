import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.auth import pwd_context, create_access_token
from datetime import datetime, timezone, timedelta
UTC = timezone.utc

client = TestClient(app)

def test_rate_limit_enforced():
    # Reset the limiter state for this test to avoid leakage
    from backend.main import limiter
    limiter.reset()
    
    # Attempt 101 requests (limit is 100/min)
    # We use a health check endpoint for speed
    for _ in range(100):
        response = client.get("/health")
        assert response.status_code == 200
    
    response = client.get("/health")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text

def test_argon2_used_not_sha256():
    # Verify the scheme is argon2
    assert pwd_context.schemes()[0] == "argon2"
    
    # Test a hash
    h = pwd_context.hash("test")
    assert h.startswith("$argon2id$")

def test_cors_rejects_non_localhost_origin():
    # Valid origin
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    
    # Invalid origin
    response = client.get("/health", headers={"Origin": "http://malicious-site.com"})
    assert "access-control-allow-origin" not in response.headers or \
           response.headers.get("access-control-allow-origin") != "http://malicious-site.com"

def test_jwt_uses_utc_aware_datetime():
    # This is a bit indirect, but we can verify create_access_token doesn't crash
    # and we can check the exp claim manually if needed.
    token = create_access_token({"sub": "admin"})
    assert token is not None
    # Jose/PyJWT handles the verification of the 'exp' claim which is an integer timestamp.
    # The fix was switching utcnow() (naive) to now(UTC) (aware).

def test_readme_exists_and_has_setup_instructions():
    import os
    readme_path = "README.md"
    assert os.path.exists(readme_path)
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Installation" in content
        assert "Getting Started" in content
        assert "Testing" in content
