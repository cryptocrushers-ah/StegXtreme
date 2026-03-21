import time
import os
import csv
import torch
import subprocess
from core.neural.trainer import GANTrainer
from core.neural.registry import ModelRegistry
from core.neural.data_loader import get_combined_loader


# ── Configuration ─────────────────────────────────────────────────────────
CONFIG = {
    "data_folder"   : "storage/training_data",
    "save_every"    : 500,
    "break_every"   : 5000,
    "train_minutes" : 20,
    "rest_minutes"  : 10,
    "max_temp"      : 89,
    "warn_temp"     : 78,
    "batch_size"    : 16,
    "patch_size"    : 128,
    "log_path"      : "storage/training_log.csv",
    "hider_path"    : "storage/models/hider_trained.pt",
    "detector_path" : "storage/models/detector_trained.pt",
}

# ── GPU Utilities ──────────────────────────────────────────────────────────
def get_gpu_temp() -> int:
    """Get current GPU temperature in Celsius"""
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        return int(result.stdout.strip())
    except:
        return 0


def get_gpu_utilization() -> int:
    """Get current GPU utilization percentage"""
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        return int(result.stdout.strip())
    except:
        return 0


def get_gpu_memory() -> str:
    """Get GPU memory usage"""
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        used, total = result.stdout.strip().split(", ")
        return f"{used}MB/{total}MB"
    except:
        return "N/A"


# ── Cooling Break ──────────────────────────────────────────────────────────
def cooling_break(minutes: int, step: int, reason: str = "scheduled"):
    """
    Pause training for cooling.
    Shows countdown with live GPU temperature.
    """
    print(f"\n{'='*60}")
    print(f"🌡️  Cooling Break — {reason}")
    print(f"📍 Step: {step}")
    print(f"⏸️  Pausing for {minutes} minutes")
    print(f"{'='*60}")

    total_seconds = minutes * 60
    start_temp    = get_gpu_temp()
    print(f"GPU temp at break start: {start_temp}°C\n")

    for remaining in range(total_seconds, 0, -15):
        temp  = get_gpu_temp()
        util  = get_gpu_utilization()
        mem   = get_gpu_memory()
        mins  = remaining // 60
        secs  = remaining % 60

        # temperature indicator
        if temp >= 80:
            temp_icon = "🔴"
        elif temp >= 70:
            temp_icon = "🟡"
        else:
            temp_icon = "🟢"

        print(
            f"Resume in {mins:02d}:{secs:02d} | "
            f"{temp_icon} GPU {temp}°C | "
            f"Util {util}% | "
            f"Mem {mem}",
            end="\r"
        )
        time.sleep(15)

    end_temp = get_gpu_temp()
    cooled   = start_temp - end_temp
    print(f"\n\n✅ Break complete")
    print(f"   Start temp : {start_temp}°C")
    print(f"   End temp   : {end_temp}°C")
    print(f"   Cooled by  : {cooled}°C")
    print(f"{'='*60}\n")


# ── Checkpoint ────────────────────────────────────────────────────────────
def save_checkpoint(trainer, registry, step, all_rows, config):
    """Save model weights and training log"""
    registry.save(trainer.hider,    config["hider_path"])
    registry.save(trainer.detector, config["detector_path"])

    with open(config["log_path"], "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["step", "d_loss", "h_loss", "gpu_temp"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n💾 Checkpoint saved — step {step}")


# ── Main Training Loop ─────────────────────────────────────────────────────
def continuous_train(config=CONFIG):

    print("="*60)
    print("   StegXtreme — Continuous GAN Training")
    print("="*60)

    # ── setup trainer ──────────────────────────────────────────
    trainer  = GANTrainer()
    registry = ModelRegistry()

    # load existing weights if available
    if os.path.exists(config["hider_path"]):
        registry.load_unsigned(
            trainer.hider, config["hider_path"]
        )
        print("✅ Loaded existing hider weights")
    else:
        print("⚠️  No existing hider weights — starting fresh")

    if os.path.exists(config["detector_path"]):
        registry.load_unsigned(
            trainer.detector, config["detector_path"]
        )
        print("✅ Loaded existing detector weights")
    else:
        print("⚠️  No existing detector weights — starting fresh")

    # ── setup data ─────────────────────────────────────────────
    loader = get_combined_loader(
        config["data_folder"],
        batch_size=config["batch_size"],
        patch_size=config.get("patch_size", 128),
        num_workers=2
    )
    use_real  = loader is not None
    data_iter = iter(loader) if use_real else None

    # ── print config ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Training mode  : {'REAL DATA ✅' if use_real else 'SYNTHETIC ⚠️'}")
    print(f"Batch size     : {config['batch_size']}")
    print(f"Save every     : {config['save_every']} steps")
    print(f"Break every    : {config['break_every']} steps")
    print(f"Session length : {config['train_minutes']} minutes")
    print(f"Break duration : {config['rest_minutes']} minutes")
    print(f"Max temp       : {config['max_temp']}°C")
    print(f"{'='*60}")
    print(f"Press Ctrl+C to stop safely\n")

    # ── training state ─────────────────────────────────────────
    step          = 0
    all_rows      = []
    session_start = time.time()
    total_start   = time.time()
    temp_history  = []

    try:
        while True:
            step += 1

            # ── get batch ──────────────────────────────────────
            if use_real:
                try:
                    cover = next(data_iter)
                except StopIteration:
                    data_iter = iter(loader)
                    cover     = next(data_iter)
            else:
                cover = torch.rand(
                    config["batch_size"], 1, 64, 64
                )

            payload = torch.rand(cover.shape)

            # ── train step ─────────────────────────────────────
            losses = trainer.train_step(cover, payload)

            # ── record ─────────────────────────────────────────
            temp = get_gpu_temp() if step % 10 == 0 else (
                temp_history[-1] if temp_history else 0
            )
            temp_history.append(temp)
            if len(temp_history) > 100:
                temp_history.pop(0)

            all_rows.append({
                "step"    : step,
                "d_loss"  : round(losses["d_loss"], 6),
                "h_loss"  : round(losses["h_loss"], 6),
                "gpu_temp": temp
            })

            # ── print progress ─────────────────────────────────
            if step % 10 == 0:
                elapsed      = (time.time() - session_start) / 60
                total_elapsed = (time.time() - total_start) / 3600
                avg_temp     = sum(temp_history) / len(temp_history)

                # temperature color
                if temp >= config["warn_temp"]:
                    temp_str = f"🔴 {temp}°C"
                elif temp >= 70:
                    temp_str = f"🟡 {temp}°C"
                else:
                    temp_str = f"🟢 {temp}°C"

                print(
                    f"Step {step:6d} | "
                    f"d={losses['d_loss']:.4f} | "
                    f"h={losses['h_loss']:.4f} | "
                    f"{temp_str} | "
                    f"Session {elapsed:.1f}m | "
                    f"Total {total_elapsed:.1f}h",
                    end="\r"
                )

            # ── save checkpoint ────────────────────────────────
            if step % config["save_every"] == 0:
                save_checkpoint(
                    trainer, registry, step, all_rows, config
                )

            # ── emergency temperature check ────────────────────
            if step % 25 == 0:
                temp = get_gpu_temp()
                if temp >= config["max_temp"]:
                    print(f"\n\n🚨 EMERGENCY STOP — GPU at {temp}°C!")
                    save_checkpoint(
                        trainer, registry, step, all_rows, config
                    )
                    cooling_break(
                        minutes=config["rest_minutes"] * 2,
                        step=step,
                        reason=f"EMERGENCY — GPU reached {temp}°C"
                    )
                    session_start = time.time()

            # ── scheduled break every 1000 steps ──────────────
            if step % config["break_every"] == 0:
                print()
                save_checkpoint(
                    trainer, registry, step, all_rows, config
                )
                cooling_break(
                    minutes=config["rest_minutes"],
                    step=step,
                    reason=f"Scheduled — every {config['break_every']} steps"
                )
                session_start = time.time()

            # ── time based break every 40 minutes ─────────────
            elapsed_mins = (time.time() - session_start) / 60
            if elapsed_mins >= config["train_minutes"]:
                print(
                    f"\n\n⏰ {config['train_minutes']} minute "
                    f"session complete"
                )
                save_checkpoint(
                    trainer, registry, step, all_rows, config
                )
                cooling_break(
                    minutes=config["rest_minutes"],
                    step=step,
                    reason=f"{config['train_minutes']} min session complete"
                )
                session_start = time.time()

    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped by user at step {step}")
        save_checkpoint(trainer, registry, step, all_rows, config)
        total_hours = (time.time() - total_start) / 3600
        temp        = get_gpu_temp()
        print(f"\n{'='*60}")
        print(f"Training Summary:")
        print(f"  Total steps  : {step}")
        print(f"  Total time   : {total_hours:.2f} hours")
        print(f"  Final GPU temp: {temp}°C")
        if all_rows:
            print(f"  Final d_loss : {all_rows[-1]['d_loss']}")
            print(f"  Final h_loss : {all_rows[-1]['h_loss']}")
        print(f"{'='*60}")
        print("✅ Models saved safely")


if __name__ == "__main__":
    continuous_train()