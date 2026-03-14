from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil
import os
import uuid
from core.backends.router import get_backend

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/api/extract")
async def extract_data(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    try:
        # Save uploaded file
        ext = file.filename.split('.')[-1]
        unique_id = str(uuid.uuid4())
        in_path = os.path.join(TEMP_DIR, f"{unique_id}_extract.{ext}")
        
        with open(in_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get appropriate backend
        BackendClass = get_backend(in_path)
        
        # Extract payload
        payload_bytes = BackendClass.extract(
            stego_path=in_path,
            password=password
        )
        
        text_payload = payload_bytes.decode('utf-8', errors='replace')
        
        return {"payload": text_payload}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
