"""
gpu_status.py — GET /api/gpu-status
=====================================
Detects GPU via (in order of preference):
  1. PyTorch CUDA
  2. nvidia-smi subprocess
  3. Returns available=False cleanly (never crashes)
"""

from fastapi import APIRouter
import subprocess

router = APIRouter()


def _detect_gpu() -> dict:
    info = {
        "available": False,
        "name": None,
        "vram_mb": None,
        "cuda_version": None,
        "utilisation_pct": None,
    }

    # ── Try PyTorch first ─────────────────────────────────────────────
    try:
        import torch
        if torch.cuda.is_available():
            idx  = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(idx)
            info.update({
                "available":    True,
                "name":         props.name,
                "vram_mb":      props.total_memory // (1024 * 1024),
                "cuda_version": torch.version.cuda,
            })
            # Utilisation via nvidia-smi
            try:
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=3,
                )
                if r.returncode == 0:
                    info["utilisation_pct"] = int(r.stdout.strip().split("\n")[0])
            except Exception:
                pass
            return info
        # torch present but CUDA not available
        return info
    except ImportError:
        pass  # no torch — try nvidia-smi

    # ── Try nvidia-smi directly ───────────────────────────────────────
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = [p.strip() for p in r.stdout.strip().split("\n")[0].split(",")]
            info.update({
                "available":       True,
                "name":            parts[0] if len(parts) > 0 else None,
                "vram_mb":         int(parts[1]) if len(parts) > 1 else None,
                "utilisation_pct": int(parts[2]) if len(parts) > 2 else None,
            })
    except Exception:
        pass  # nvidia-smi not found or failed — stays available=False

    return info


@router.get("/api/gpu-status")
async def gpu_status():
    return _detect_gpu()
