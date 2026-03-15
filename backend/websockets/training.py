from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import torch
import json
from core.neural.trainer import GANTrainer
from starlette.websockets import WebSocketState

# store active training sessions
active_sessions = {}

async def training_ws_endpoint(
    websocket: WebSocket,
    run_id: str
):
    """
    WebSocket endpoint that streams training metrics live.
    Streams d_loss, h_loss, epoch per step.
    """
    await websocket.accept()
    active_sessions[run_id] = websocket

    trainer = GANTrainer()
    cover   = torch.rand(2, 1, 64, 64)
    payload = torch.rand(2, 1, 64, 64)

    try:
        for step in range(200):
            # run one training step
            losses = trainer.train_step(cover, payload)

            # stream metrics to React
            await websocket.send_json({
                "run_id" : run_id,
                "step"   : step + 1,
                "d_loss" : round(losses["d_loss"], 6),
                "h_loss" : round(losses["h_loss"], 6),
                "epoch"  : step // 10 + 1
            })

            # small delay so frontend can render
            await asyncio.sleep(0.05)

        await websocket.send_json({
            "run_id"  : run_id,
            "status"  : "complete",
            "message" : "Training finished"
        })

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected from run {run_id}")
    except Exception as exc:
        print(f"[WS] Error in run {run_id}: {exc}")
    finally:
        active_sessions.pop(run_id, None)
        # Check if the websocket is still open before trying to close it.
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass