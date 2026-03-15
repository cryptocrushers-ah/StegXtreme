try:
    import torch
    import cupy as cp
except ImportError:
    cp = None
    torch = None

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(cp is None or torch is None, reason="cupy or torch not installed")


def get_gpu_memory_mb():
    """Returns current GPU memory usage in MB"""
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / 1024 / 1024
    return cp.get_default_memory_pool().used_bytes() / 1024 / 1024

def test_100_embeds_no_memory_leak():
    """GPU memory must not grow across 100 consecutive embeds"""
    frame = np.random.rand(256, 256).astype(np.float32)
    bits  = np.random.randint(0, 2, 256).astype(np.int8)

    # warmup
    for _ in range(5):
        LL, LH, HL, HH = dwt2(frame)
        region = LL.ravel().copy()
        ss_embed(region, bits, n=1, seed=42, strength=18.0)
        free()

    # measure baseline
    free()
    baseline_mb = get_gpu_memory_mb()

    # run 100 embeds
    for _ in range(100):
        LL, LH, HL, HH = dwt2(frame)
        region = LL.ravel().copy()
        ss_embed(region, bits, n=1, seed=42, strength=18.0)
        free()

    final_mb = get_gpu_memory_mb()
    growth   = final_mb - baseline_mb

    print(f"\nBaseline: {baseline_mb:.2f} MB")
    print(f"Final:    {final_mb:.2f} MB")
    print(f"Growth:   {growth:.2f} MB")

    # allow max 10MB growth
    assert growth < 10.0, f"Memory leak detected: {growth:.2f} MB growth"

def test_full_embed_analyze_flow():
    """Full pipeline: embed → extract → verify"""
    from core.compute.backend import ss_embed, ss_extract

    # create test data
    region = np.zeros(256 * 4, dtype=np.float32)
    bits   = np.array([1, 0, 1, 1], dtype=np.int8)

    # embed
    ss_embed(region, bits, n=4, seed=42, strength=18.0)

    # extract
    extracted = ss_extract(region, n=4, seed=42)

    # verify
    np.testing.assert_array_equal(
        extracted, bits,
        err_msg="Extracted bits don't match embedded bits"
    )

def test_model_save_load_inference():
    """Save model, reload it, verify inference still works"""
    import tempfile
    import os

    model    = HiderNetwork()
    registry = ModelRegistry()

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "hider.pt")
        registry.save(model, path)

        loaded = registry.load(HiderNetwork(), path)
        loaded.eval()

        cover   = torch.rand(1, 1, 64, 64)
        payload = torch.rand(1, 1, 64, 64)

        with torch.no_grad():
            out = loaded(cover, payload)

        assert out.shape == (1, 1, 64, 64)
        assert not torch.isnan(out).any()

def test_gan_200_steps_losses_finite():
    """Run 200 training steps, all losses must be finite"""
    import math
    trainer = GANTrainer()
    cover   = torch.rand(2, 1, 64, 64)
    payload = torch.rand(2, 1, 64, 64)

    for step in range(200):
        losses = trainer.train_step(cover, payload)
        assert math.isfinite(losses["d_loss"]), \
            f"d_loss NaN at step {step}"
        assert math.isfinite(losses["h_loss"]), \
            f"h_loss NaN at step {step}"