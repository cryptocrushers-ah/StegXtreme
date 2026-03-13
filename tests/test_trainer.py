import torch
import math
import pytest
from core.neural.trainer import GANTrainer
from core.neural.registry import ModelRegistry
from core.neural.hider import HiderNetwork

# shared inputs
B, H, W  = 2, 64, 64
COVER    = torch.rand(B, 1, H, W)
PAYLOADS = torch.rand(B, 1, H, W)

def test_gan_train_step_returns_finite_losses():
    trainer = GANTrainer()
    losses  = trainer.train_step(COVER, PAYLOADS)
    assert "d_loss" in losses
    assert "h_loss" in losses
    assert math.isfinite(losses["d_loss"]), "d_loss is not finite"
    assert math.isfinite(losses["h_loss"]), "h_loss is not finite"

def test_gan_train_step_returns_floats():
    trainer = GANTrainer()
    losses  = trainer.train_step(COVER, PAYLOADS)
    assert isinstance(losses["d_loss"], float)
    assert isinstance(losses["h_loss"], float)

def test_gan_10_steps_no_nan():
    trainer = GANTrainer()
    for i in range(10):
        losses = trainer.train_step(COVER, PAYLOADS)
        assert math.isfinite(losses["d_loss"]), f"NaN at step {i}"
        assert math.isfinite(losses["h_loss"]), f"NaN at step {i}"

def test_model_save_and_load(tmp_path):
    model    = HiderNetwork()
    registry = ModelRegistry()
    path     = str(tmp_path / "hider.pt")
    registry.save(model, path)
    loaded = registry.load(HiderNetwork(), path)
    # verify weights match
    for p1, p2 in zip(model.parameters(), loaded.parameters()):
        assert torch.equal(p1, p2)