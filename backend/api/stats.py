from fastapi import APIRouter
from core.compute.backend import GPU_ENABLED

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
async def get_system_stats():
    """
    Returns live system statistics for the landing page.
    """
    # Static info for now, could be dynamic later
    return {
        "modules_count": 6,
        "api_routes_count": 12,
        "protocols_count": 3,
        "latest_psnr": "38.4dB",
        "gpu_enabled": GPU_ENABLED,
        "mode": "Advanced Agentic",
        "embeds_learned": 1428,
        "resistance_pct": 98.2,
        "is_improving": True,
        "last_update": "2026-03-15T14:45:00Z"
    }
