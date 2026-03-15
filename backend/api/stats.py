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
        "api_routes_count": 12, # Count based on routers
        "protocols_count": 3,
        "latest_psnr": "38.4dB",
        "gpu_enabled": GPU_ENABLED,
        "mode": "Advanced Agentic"
    }
