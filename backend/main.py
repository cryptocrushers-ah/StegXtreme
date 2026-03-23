try:
    import cupy as cp
except Exception:
    pass

#import torch
#if torch.cuda.is_available():
#    torch.cuda.init()

from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.websockets.training import training_ws_endpoint
from backend.api import embed, extract, analyze, visualise, tunnel, auth, stats, receive, threat
from backend.api.auth import get_current_user

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from backend.api import auth_verify
from backend.api import gpu_status

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(title="StegXtreme")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/system/gpu")
async def get_gpu_status():
    cupy_av = False
    name = None
    try:
        import cupy
        cupy_av = True
        name = cupy.cuda.runtime.getDeviceProperties(0)['name'].decode()
    except Exception:
        pass

    torch_cuda = False
    try:
        import torch
        torch_cuda = torch.cuda.is_available()
        if torch_cuda and not name:
            name = torch.cuda.get_device_name(0)
    except Exception:
        pass

    total_mb, used_mb = 0, 0
    if torch_cuda:
        try:
            free, total = torch.cuda.mem_get_info()
            total_mb = total // (1024 * 1024)
            used_mb = (total - free) // (1024 * 1024)
        except Exception:
            pass
    elif cupy_av:
        try:
            free, total = cupy.cuda.runtime.memGetInfo()
            total_mb = total // (1024 * 1024)
            used_mb = (total - free) // (1024 * 1024)
        except Exception:
            pass
            
    return {
        "cupy_available": cupy_av,
        "torch_cuda_available": torch_cuda,
        "gpu_name": name,
        "vram_total_mb": total_mb,
        "vram_used_mb": used_mb
    }

@app.websocket("/ws/training/{run_id}")
async def training_websocket(websocket: WebSocket, run_id: str):
    await training_ws_endpoint(websocket, run_id)

app.include_router(gpu_status.router)
app.include_router(stats.router)
app.include_router(auth.router)
app.include_router(embed.router, dependencies=[Depends(get_current_user)])
app.include_router(extract.router, dependencies=[Depends(get_current_user)])
app.include_router(analyze.router, dependencies=[Depends(get_current_user)])
app.include_router(visualise.router, dependencies=[Depends(get_current_user)])
app.include_router(tunnel.router)
app.include_router(receive.router)
app.include_router(threat.router, dependencies=[Depends(get_current_user)])
app.include_router(auth_verify.router)
