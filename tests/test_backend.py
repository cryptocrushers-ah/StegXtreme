import numpy as np
import pytest
from core.compute import backend

RNG = np.random.default_rng(42)
SAMPLE_ARR = RNG.random((64, 64)).astype(np.float32)

def test_dwt_roundtrip():
    LL, LH, HL, HH = backend.dwt2(SAMPLE_ARR)
    assert LL.shape == (32, 32)
    assert isinstance(LL, np.ndarray)

def test_carrier_shape():
    cars = backend.make_carriers(10, 256, seed=0)
    assert cars.shape == (10, 256)

def test_carrier_values_plus_minus_one():
    cars = backend.make_carriers(10, 256, seed=0)
    assert set(np.unique(cars).tolist()).issubset({-1.0, 1.0})

def test_ss_embed_extract_roundtrip():
    region = np.zeros(256 * 4, dtype=np.float32)
    bits = np.array([1, 0, 1, 1], dtype=np.int8)
    backend.ss_embed(region, bits, n=4, seed=7, strength=18.0)
    extracted = backend.ss_extract(region, n=4, seed=7)
    np.testing.assert_array_equal(extracted, bits)

def test_to_device_returns_array():
    gpu = backend.to_device(SAMPLE_ARR)
    assert gpu is not None
    assert hasattr(gpu, 'shape')

def test_to_cpu_returns_numpy():
    gpu = backend.to_device(SAMPLE_ARR)
    cpu = backend.to_cpu(gpu)
    assert isinstance(cpu, np.ndarray)
    np.testing.assert_allclose(cpu, SAMPLE_ARR)

def test_free_no_crash():
    backend.free()

def test_gpu_cpu_output_identical():
    # GPU path result
    LL_gpu, _, _, _ = backend.dwt2(SAMPLE_ARR)

    # Pure NumPy reference
    f = SAMPLE_ARR.astype(np.float32)
    L = (f[:, 0::2] + f[:, 1::2]) * 0.5
    LL_cpu = (L[0::2, :] + L[1::2, :]) * 0.5

    np.testing.assert_allclose(LL_gpu, LL_cpu, rtol=1e-5)