import csv
import time
import torch
from core.neural.trainer import GANTrainer
from core.neural.registry import ModelRegistry

def run_full_training(steps=200, log_path="storage/training_log.csv"):
    """
    Run full GAN training for 200 steps.
    Saves loss to CSV and model weights at end.
    """
    trainer  = GANTrainer()
    registry = ModelRegistry()

    cover    = torch.rand(4, 1, 64, 64)
    payload  = torch.rand(4, 1, 64, 64)

    rows = []
    print(f"Starting GAN training for {steps} steps...\n")

    for step in range(1, steps + 1):
        losses = trainer.train_step(cover, payload)

        row = {
            "step"   : step,
            "d_loss" : round(losses["d_loss"], 6),
            "h_loss" : round(losses["h_loss"], 6),
            "epoch"  : step // 10 + 1
        }
        rows.append(row)

        if step % 20 == 0:
            print(f"Step {step:3d}/200 | "
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

    # save model weights
    registry.save(
        trainer.hider,
        "storage/models/hider_trained.pt"
    )
    registry.save(
        trainer.detector,
        "storage/models/detector_trained.pt"
    )
    print("Models saved to storage/models/")

    # verify detection rate drops
    first_10  = sum(r["d_loss"] for r in rows[:10])  / 10
    last_10   = sum(r["d_loss"] for r in rows[-10:]) / 10
    print(f"\nFirst 10 steps avg d_loss: {first_10:.4f}")
    print(f"Last  10 steps avg d_loss: {last_10:.4f}")
    if last_10 < first_10:
        print("✅ Detection loss decreasing — model learning")
    else:
        print("⚠️  Detection loss not decreasing — may need more steps")

    return rows

if __name__ == "__main__":
    run_full_training()