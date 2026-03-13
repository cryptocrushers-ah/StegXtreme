import torch
import numpy as np
import pytest
from core.neural.hider import HiderNetwork
from core.neural.detector import DetectorNetwork

# shared test inputs
COVER   = torch.zeros(1, 1, 64, 64)
PAYLOAD = torch.zeros(1, 1, 64, 64)
FRAME   = torch.zeros(1, 1, 64, 64)

# ── Hider tests ──────────────────────────────────────────────────────────

def test_neural_hider_output_shape():
    model = HiderNetwork().eval()
    with torch.no_grad():
        out = model(COVER, PAYLOAD)
    assert out.shape == (1, 1, 64, 64), f"Wrong shape: {out.shape}"

def test_neural_hider_no_nan():
    model = HiderNetwork().eval()
    with torch.no_grad():
        out = model(COVER, PAYLOAD)
    assert not torch.isnan(out).any(), "HiderNetwork output contains NaN"

def test_neural_hider_residual_is_small():
    # Tanh output should be between -1 and 1
    model = HiderNetwork().eval()
    with torch.no_grad():
        out = model(COVER, PAYLOAD)
    assert out.abs().max().item() <= 1.0

# ── Detector tests ───────────────────────────────────────────────────────

def test_neural_detector_output_between_0_and_1():
    model = DetectorNetwork().eval()
    with torch.no_grad():
        out = model(FRAME)
    val = out.item()
    assert 0.0 <= val <= 1.0, f"Out of range: {val}"

def test_neural_detector_output_shape():
    model = DetectorNetwork().eval()
    with torch.no_grad():
        out = model(FRAME)
    assert out.shape == (1, 1)

def test_neural_detector_no_nan():
    model = DetectorNetwork().eval()
    with torch.no_grad():
        out = model(FRAME)
    assert not torch.isnan(out).any()

# ── ONNX tests ───────────────────────────────────────────────────────────

def test_onnx_loads_without_error():
    import onnxruntime as ort
    hider_session    = ort.InferenceSession("storage/models/hider.onnx")
    detector_session = ort.InferenceSession("storage/models/detector.onnx")
    assert hider_session is not None
    assert detector_session is not None