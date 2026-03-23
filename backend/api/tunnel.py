from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from backend.api.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import asyncio

from core.tunnel.dns import DNSTunnel
from core.tunnel.http import HTTPTunnel

router = APIRouter(prefix="/api/tunnel", tags=["tunnel"])

# Simple in-memory WebSocket manager for traffic logs
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            msg_str = json.dumps(message)
            for connection in self.active_connections[session_id]:
                await connection.send_text(msg_str)

manager = ConnectionManager()

# Track active transmissions for cancellation
active_transmissions: Dict[str, bool] = {}

class TunnelSendRequest(BaseModel):
    protocol: str # "dns" or "http"
    payload: str
    target: str # IP or URL
    session_id: str

@router.post("/send", dependencies=[Depends(get_current_user)])
async def tunnel_send(req: TunnelSendRequest):
    payload_bytes = req.payload.encode('utf-8')
    
    # Log the outgoing packet
    await manager.broadcast(req.session_id, {
        "direction": "OUT",
        "protocol": req.protocol.upper(),
        "payload": req.payload,
        "target": req.target,
        "timestamp": asyncio.get_event_loop().time()
    })

    active_transmissions[req.session_id] = False
    
    try:
        def should_stop():
            return active_transmissions.get(req.session_id, False)

        loop = asyncio.get_event_loop()
        if req.protocol.lower() == "dns":
            await loop.run_in_executor(None, DNSTunnel.send, payload_bytes, req.target, req.session_id, should_stop)
        elif req.protocol.lower() == "http":
            # Even if HTTP is one request, running in executor avoids blocking event loop
            await loop.run_in_executor(None, HTTPTunnel.send, payload_bytes, req.target)
        else:
            raise HTTPException(status_code=400, detail="Unsupported protocol")
            
        if should_stop():
            return {"status": "cancelled"}
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        active_transmissions.pop(req.session_id, None)

@router.post("/receive")
async def tunnel_receive(request: Request):
    # This endpoint receives incoming HTTP tunnel requests
    headers = dict(request.headers)
    payload_bytes = HTTPTunnel.receive_from_headers(headers)
    
    if payload_bytes:
        payload_str = payload_bytes.decode('utf-8', errors='ignore')
        # In a real scenario, we'd need to know the session_id from headers too.
        # For simplicity, we'll use a "broadcast_all" or specific header.
        session_id = headers.get("X-Session-ID", "global")
        
        await manager.broadcast(session_id, {
            "direction": "IN",
            "protocol": "HTTP",
            "payload": payload_str,
            "timestamp": asyncio.get_event_loop().time()
        })
        return {"status": "received", "payload": payload_str}
    
    return {"status": "no_payload"}

# WebSocket endpoint for live traffic
@router.websocket("/ws/traffic/{session_id}")
async def traffic_ws(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Just keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
