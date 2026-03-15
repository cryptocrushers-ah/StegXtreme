from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.websockets.training import training_ws_endpoint
from backend.api import embed, extract, analyze, visualise

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

app.include_router(embed.router)
app.include_router(extract.router)
app.include_router(analyze.router)
app.include_router(visualise.router)
