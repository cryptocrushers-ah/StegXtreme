import csv
import torch
from core.neural.trainer import GANTrainer
from core.neural.registry import ModelRegistry
from core.neural.data_loader import get_combined_loader

def run_full_training(
    steps=200,
    data_folder="storage/training_data",
    log_path="storage/training_log.csv"
):
    trainer  = GANTrainer()
    registry = ModelRegistry()

    # try real data first, fall back to synthetic
    loader      = get_combined_loader(data_folder, batch_size=4)
    use_real    = loader is not None
    data_iter   = iter(loader) if use_real else None

    print(f"Training mode: {'REAL DATA' if use_real else 'SYNTHETIC'}")
    print(f"Starting GAN training for {steps} steps...\n")

    rows = []

    for step in range(1, steps + 1):
        # get batch
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

        row = {
            "step"   : step,
            "d_loss" : round(losses["d_loss"], 6),
            "h_loss" : round(losses["h_loss"], 6),
            "epoch"  : step // 10 + 1
        }
        rows.append(row)

        if step % 20 == 0:
            print(f"Step {step:3d}/{steps} | "
                  f"d_loss={losses['d_loss']:.4f} | "
                  f"h_loss={losses['h_loss']:.4f}")

    # save CSV log
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["step", "d_loss", "h_loss", "epoch"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nLog saved to {log_path}")

    # save models
    registry.save(trainer.hider,    "storage/models/hider_trained.pt")
    registry.save(trainer.detector, "storage/models/detector_trained.pt")
    print("Models saved!")

    return rows

if __name__ == "__main__":
    run_full_training()