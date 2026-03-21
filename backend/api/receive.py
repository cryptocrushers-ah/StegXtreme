from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.tunnel.receiver import TunnelReceiver
from backend.tunnel import lan_utils

router = APIRouter(prefix="/api/tunnel/receive", tags=["Tunnel"])

class StartRequest(BaseModel):
    port: int = 9000

class MessageResponse(BaseModel):
    id: str
    timestamp: str
    session_id: str
    protocol: str
    sender_ip: str
    payload: str
    chunks_received: int
    decode_time_ms: float

class StatusResponse(BaseModel):
    listening: bool
    port: Optional[int]
    lan_ip: Optional[str]
    shareable_url: Optional[str]

# Global receiver instance
_receiver: Optional[TunnelReceiver] = None
_current_port: Optional[int] = None

@router.post("/start")
async def start_receiver(req: StartRequest):
    global _receiver, _current_port
    
    if _receiver and _receiver.is_running:
        raise HTTPException(status_code=400, detail="Receiver is already running")
    
    if not lan_utils.check_port_available(req.port):
        raise HTTPException(status_code=400, detail=f"Port {req.port} is already in use")
    
    _receiver = TunnelReceiver(port=req.port)
    _receiver.start()
    _current_port = req.port
    
    lan_ip = lan_utils.get_local_ip()
    shareable_url = lan_utils.get_shareable_url(req.port)
    
    return {
        "status": "listening",
        "port": req.port,
        "lan_ip": lan_ip,
        "shareable_url": shareable_url
    }

@router.post("/stop")
async def stop_receiver():
    global _receiver, _current_port
    
    if not _receiver or not _receiver.is_running:
        return {"status": "already_stopped"}
    
    _receiver.stop()
    _current_port = None
    
    return {"status": "stopped"}

@router.get("/messages")
async def get_messages():
    if not _receiver:
        return {"messages": [], "count": 0}
    
    messages = _receiver.get_messages()
    return {"messages": messages, "count": len(messages)}

@router.get("/status")
async def get_status():
    global _receiver, _current_port
    
    is_running = _receiver.is_running if _receiver else False
    
    if is_running:
        lan_ip = lan_utils.get_local_ip()
        return {
            "listening": True,
            "port": _current_port,
            "lan_ip": lan_ip,
            "shareable_url": lan_utils.get_shareable_url(_current_port)
        }
    else:
        return {
            "listening": False,
            "port": 9000,
            "lan_ip": "",
            "shareable_url": ""
        }

@router.delete("/messages")
async def clear_messages():
    if not _receiver:
        return {"status": "success", "cleared": 0}
    
    cleared = _receiver.clear_messages()
    return {"status": "success", "cleared": cleared}
