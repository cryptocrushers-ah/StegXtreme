from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.websockets.training import training_ws_endpoint
from backend.api import embed, extract, analyze, visualise, tunnel, auth, stats, receive, threat
from backend.api.auth import get_current_user

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app = FastAPI(title="StegXtreme")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws/training/{run_id}")
async def training_websocket(websocket: WebSocket, run_id: str):
    await training_ws_endpoint(websocket, run_id)

app.include_router(stats.router)
app.include_router(auth.router)
app.include_router(embed.router, dependencies=[Depends(get_current_user)])
app.include_router(extract.router, dependencies=[Depends(get_current_user)])
app.include_router(analyze.router, dependencies=[Depends(get_current_user)])
app.include_router(visualise.router, dependencies=[Depends(get_current_user)])
app.include_router(tunnel.router, dependencies=[Depends(get_current_user)])
app.include_router(receive.router)
app.include_router(threat.router, dependencies=[Depends(get_current_user)])
