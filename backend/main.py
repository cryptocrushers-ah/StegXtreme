from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.websockets.training import training_ws_endpoint
from backend.api import embed, extract, analyze, visualise, tunnel, auth
from backend.api.auth import get_current_user

app = FastAPI(title="StegXtreme")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws/training/{run_id}")
async def training_websocket(websocket: WebSocket, run_id: str):
    await training_ws_endpoint(websocket, run_id)

app.include_router(auth.router)
app.include_router(embed.router, dependencies=[Depends(get_current_user)])
app.include_router(extract.router, dependencies=[Depends(get_current_user)])
app.include_router(analyze.router, dependencies=[Depends(get_current_user)])
app.include_router(visualise.router, dependencies=[Depends(get_current_user)])
app.include_router(tunnel.router, dependencies=[Depends(get_current_user)])
