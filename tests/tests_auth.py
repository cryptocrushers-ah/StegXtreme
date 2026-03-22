import os
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from core.compute.auth import (
    generate_keypair, hash_pixels,
    sign_and_embed, verify_image
)

# ── Helpers ───────────────────────────────────────────────────────────────
def make_test_image(path, w=128, h=128):
    arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    Image.fromarray(arr).save(path)

# ── Tests ─────────────────────────────────────────────────────────────────
def test_hash_pixels_is_deterministic(tmp_path):
    img = str(tmp_path / "test.png")
    make_test_image(img)
    assert hash_pixels(img) == hash_pixels(img)

def test_hash_changes_after_pixel_edit(tmp_path):
    img = str(tmp_path / "test.png")
    make_test_image(img)
    h1  = hash_pixels(img)
    # change one pixel
    pil = Image.open(img)
    arr = np.array(pil)
    arr[0, 0, 0] = (arr[0, 0, 0] + 1) % 255
    Image.fromarray(arr).save(img)
    h2  = hash_pixels(img)
    assert h1 != h2

def test_sign_returns_valid_signature(tmp_path):
    img     = str(tmp_path / "test.png")
    out     = str(tmp_path / "signed.png")
    make_test_image(img)
    priv, _ = generate_keypair()
    # use sign_and_embed instead of sign_image
    result  = sign_and_embed(img, priv, out)
    assert result == True
    # verify output exists and is valid
    assert os.path.exists(out)

def test_embed_and_verify_roundtrip(tmp_path):
    img  = str(tmp_path / "test.png")
    out  = str(tmp_path / "signed.png")
    make_test_image(img, 256, 256)
    priv, _ = generate_keypair()
    result  = sign_and_embed(img, priv, out)
    assert result == True
    verify  = verify_image(out)
    assert verify.verdict == "AUTHENTIC"
    assert verify.is_authentic == True

def test_tampered_image_detected(tmp_path):
    img  = str(tmp_path / "test.png")
    out  = str(tmp_path / "signed.png")
    make_test_image(img, 256, 256)
    priv, _ = generate_keypair()
    sign_and_embed(img, priv, out)
    # tamper with signed image
    pil = Image.open(out)
    arr = np.array(pil)
    arr[10, 10, 0] = (arr[10, 10, 0] + 50) % 255
    Image.fromarray(arr).save(out)
    verify = verify_image(out)
    assert verify.verdict == "TAMPERED"
    assert verify.modification_detected == True

def test_unsigned_image_returns_unsigned(tmp_path):
    img = str(tmp_path / "unsigned.png")
    make_test_image(img, 256, 256)
    result = verify_image(img)
    assert result.verdict in ["UNSIGNED", "ERROR"]

def test_sign_and_embed_does_not_raise(tmp_path):
    img  = str(tmp_path / "test.png")
    out  = str(tmp_path / "out.png")
    make_test_image(img, 256, 256)
    priv, _ = generate_keypair()
    result  = sign_and_embed(img, priv, out)
    assert isinstance(result, bool)

def test_verify_endpoint_authentic(tmp_path):
    from backend.main import app
    img  = str(tmp_path / "test.png")
    out  = str(tmp_path / "signed.png")
    make_test_image(img, 256, 256)
    from core.neural.registry import _auth_private_key
    sign_and_embed(img, _auth_private_key, out)
    client = TestClient(app)
    resp   = client.post(
        "/api/auth/verify",
        json={"file_path": out}
    )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "AUTHENTIC"

def test_verify_endpoint_tampered(tmp_path):
    from backend.main import app
    img  = str(tmp_path / "test.png")
    out  = str(tmp_path / "signed.png")
    make_test_image(img, 256, 256)
    from core.neural.registry import _auth_private_key
    sign_and_embed(img, _auth_private_key, out)
    # tamper
    pil = Image.open(out)
    arr = np.array(pil)
    arr[5, 5, 0] = (arr[5, 5, 0] + 50) % 255
    Image.fromarray(arr).save(out)
    client = TestClient(app)
    resp   = client.post(
        "/api/auth/verify",
        json={"file_path": out}
    )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "TAMPERED"