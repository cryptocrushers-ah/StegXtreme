import pytest
import numpy as np
from core.neural.traffic_mimic import TrafficMimic

mimic = TrafficMimic()

def test_traffic_mimic_untrained_returns_fallback():
    delay = mimic.next_delay([0.1] * 10)
    assert delay == 0.1

def test_traffic_mimic_delay_in_range():
    mimic.train_on_synthetic(n_samples=500)
    for _ in range(100):
        recent = list(np.random.uniform(0.05, 2.0, 10))
        delay  = mimic.next_delay(recent)
        assert 0.05 <= delay <= 2.0, f"Delay out of range: {delay}"

def test_traffic_mimic_trained_flag():
    m = TrafficMimic()
    assert m.trained == False
    m.train_on_synthetic(n_samples=100)
    assert m.trained == True

def test_traffic_mimic_output_is_float():
    mimic.train_on_synthetic(n_samples=100)
    delay = mimic.next_delay([0.1] * 10)
    assert isinstance(delay, float)

def test_traffic_mimic_onnx_export(tmp_path):
    m    = TrafficMimic()
    m.train_on_synthetic(n_samples=100)
    path = str(tmp_path / "traffic_mimic.onnx")
    m.export_onnx(path)
    import onnxruntime as ort
    session = ort.InferenceSession(path)
    assert session is not None