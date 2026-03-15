import os
import shutil
import uuid
import cv2  # type: ignore
from typing import Dict, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile  # type: ignore
from pydantic import BaseModel  # type: ignore

from core.visualiser.bitplane import render_bitplanes  # type: ignore
from core.visualiser.heatmap import render_heatmap  # type: ignore
from core.visualiser.timeline import render_timeline  # type: ignore

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

class VisualiseResponse(BaseModel):
    image_base64: str

def _save_temp_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "file")[1]
    uid = str(uuid.uuid4())
    in_path = os.path.join(TEMP_DIR, f"{uid}_vis{ext}")

    with open(in_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    return in_path

def _cleanup_temp_file(path: str):
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

@router.post("/api/visualise/bitplane", response_model=VisualiseResponse)
async def visualise_bitplane(file: UploadFile = File(...)):
    in_path = _save_temp_file(file)
    try:
        frame = cv2.imread(in_path)
        if frame is None:
            raise HTTPException(status_code=400, detail="Cannot read image file.")
            
        b64 = render_bitplanes(frame)
        return {"image_base64": b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        _cleanup_temp_file(in_path)

@router.post("/api/visualise/heatmap", response_model=VisualiseResponse)
async def visualise_heatmap(file: UploadFile = File(...)):
    in_path = _save_temp_file(file)
    try:
        frame = cv2.imread(in_path)
        if frame is None:
            raise HTTPException(status_code=400, detail="Cannot read image file.")
            
        b64 = render_heatmap(frame)
        return {"image_base64": b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        _cleanup_temp_file(in_path)


@router.post("/api/visualise/timeline", response_model=VisualiseResponse)
async def visualise_timeline(
    file: UploadFile = File(...), 
    n_frames: int = Form(30)
):
    in_path = _save_temp_file(file)
    try:
        b64 = render_timeline(in_path, n_frames=n_frames)
        return {"image_base64": b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        _cleanup_temp_file(in_path)
