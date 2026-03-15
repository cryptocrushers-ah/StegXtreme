import time
import os
import torch
from core.neural.trainer import GANTrainer
from core.neural.registry import ModelRegistry
from core.neural.data_loader import get_combined_loader

def continuous_train(
    data_folder="storage/training_data",
    save_every=50
):
    trainer  = GANTrainer()
    registry = ModelRegistry()

    # load existing weights
    hider_path    = "storage/models/hider_trained.pt"
    detector_path = "storage/models/detector_trained.pt"
    if os.path.exists(hider_path):
        registry.load_unsigned(trainer.hider, hider_path)
        print("✅ Loaded existing hider weights")
    if os.path.exists(detector_path):
        registry.load_unsigned(trainer.detector, detector_path)
        print("✅ Loaded existing detector weights")

    # get data
    loader    = get_combined_loader(data_folder, batch_size=4)
    use_real  = loader is not None
    data_iter = iter(loader) if use_real else None

    print(f"Training mode: {'REAL DATA' if use_real else 'SYNTHETIC'}")
    print("Press Ctrl+C to stop\n")

    step = 0
    try:
        while True:
            step += 1
            if use_real:
                try:
                    cover = next(data_iter)
                except StopIteration:
                    data_iter = iter(loader)
                    cover     = next(data_iter)
            else:
                cover = torch.rand(4, 1, 64, 64)

            payload = torch.rand(cover.shape)
            losses  = trainer.train_step(cover, payload)

            if step % 10 == 0:
                print(f"Step {step:5d} | "
                      f"d_loss={losses['d_loss']:.4f} | "
                      f"h_loss={losses['h_loss']:.4f}")

            if step % save_every == 0:
                registry.save(
                    trainer.hider,
                    "storage/models/hider_trained.pt"
                )
                registry.save(
                    trainer.detector,
                    "storage/models/detector_trained.pt"
                )
                print(f"💾 Saved checkpoint at step {step}")

    except KeyboardInterrupt:
        print(f"\nStopped at step {step} — saving...")
        registry.save(
            trainer.hider,
            "storage/models/hider_trained.pt"
        )
        registry.save(
            trainer.detector,
            "storage/models/detector_trained.pt"
        )
        print("✅ Final model saved")

if __name__ == "__main__":
    continuous_train()