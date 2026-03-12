# tests/test_backend.py
import numpy as np
import pytest
from core.compute import backend

# Shared test data
RNG = np.random.default_rng(42)
SAMPLE_ARR = RNG.random((64, 64), dtype=np.float32)

# ── 1. dwt2 ──────────────────────────────────────────────────────────────
def test_dwt2_output_shape():
    LL, LH, HL, HH = backend.dwt2(SAMPLE_ARR)
    assert LL.shape == (32, 32)

def test_dwt2_returns_numpy():
    results = backend.dwt2(SAMPLE_ARR)
    for band in results:
        assert isinstance(band, np.ndarray), "dwt2 must return numpy arrays"

def test_dwt2_values():
    # Compare GPU result vs pure numpy reference
    f = SAMPLE_ARR.astype(np.float32)
    L  = (f[:,0::2] + f[:,1::2]) * 0.5
    LL_ref = (L[0::2,:] + L[1::2,:]) * 0.5
    LL, _, _, _ = backend.dwt2(SAMPLE_ARR)
    np.testing.assert_allclose(LL, LL_ref, rtol=1e-5)

# ── 2. make_carriers ─────────────────────────────────────────────────────
def test_make_carriers_shape():
    cars = backend.make_carriers(10, 256, seed=0)
    assert cars.shape == (10, 256)

def test_make_carriers_values():
    # Values must be -1 or +1 only
    cars = backend.make_carriers(10, 256, seed=0)
    assert set(np.unique(cars)).issubset({-1.0, 1.0})

def test_make_carriers_deterministic():
    a = backend.make_carriers(10, 256, seed=99)
    b = backend.make_carriers(10, 256, seed=99)
    np.testing.assert_array_equal(a, b)

# ── 3. to_device / to_cpu ────────────────────────────────────────────────
def test_to_device_and_back():
    gpu = backend.to_device(SAMPLE_ARR)
    cpu = backend.to_cpu(gpu)
    np.testing.assert_allclose(cpu, SAMPLE_ARR)

# ── 4. free ──────────────────────────────────────────────────────────────
def test_free_runs_without_error():
    backend.free()  # just must not raise