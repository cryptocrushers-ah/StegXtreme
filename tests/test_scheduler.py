import numpy as np
import pytest
from core.neural.scheduler import StrengthScheduler

s = StrengthScheduler()

def test_scheduler_always_in_range():
    rng = np.random.default_rng(0)
    for _ in range(100):
        LH = rng.random((32, 32)).astype(np.float32)
        HL = rng.random((32, 32)).astype(np.float32)
        result = s.compute(LH, HL)
        assert 8.0 <= result <= 40.0, f"Out of range: {result}"

def test_scheduler_returns_float():
    LH = np.ones((32, 32), dtype=np.float32)
    HL = np.ones((32, 32), dtype=np.float32)
    result = s.compute(LH, HL)
    assert isinstance(result, float)

def test_scheduler_base_strength():
    # Zero std arrays should return close to base 18.0
    LH = np.zeros((32, 32), dtype=np.float32)
    HL = np.zeros((32, 32), dtype=np.float32)
    result = s.compute(LH, HL)
    assert result == 18.0

def test_scheduler_high_std_scales_up():
    # High variance should push strength above 18.0
    rng = np.random.default_rng(1)
    LH = rng.random((32, 32)).astype(np.float32) * 10
    HL = rng.random((32, 32)).astype(np.float32) * 10
    result = s.compute(LH, HL)
    assert result > 18.0