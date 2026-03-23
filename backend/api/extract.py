from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.utils.validation import validate_file
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
    password: str = Form(...),
    algorithm: str = Form("default")
):
    """
    Extracts a secret payload from a stego-media file.
    """
    await validate_file(file)
    if file.size > 2048 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Stego file exceeds the 2GB limit.")

    # Save uploaded file
    # The instruction changes the filename generation and file writing method.
    # Original: unique_id + ext, shutil.copyfileobj
    # New: original filename, await file.read()
    # Using TEMP_DIR as STORAGE_TEMP is not defined in the original code.
    in_path = os.path.join(TEMP_DIR, file.filename)
    try:
        with open(in_path, "wb") as f:
            f.write(await file.read())
            
        # Get appropriate backend
        BackendClass = get_backend(in_path)
        
        # Extract payload
        payload_bytes = BackendClass.extract(
            stego_path=in_path,
            password=password,
            algorithm=algorithm
        )
        
        # Attempt to decode as UTF-8 for display, but keep raw bytes
        import base64
        
        is_binary = False
        try:
            # Check if it's valid UTF-8 and contains no null bytes (common in binary)
            text_payload = payload_bytes.decode('utf-8')
            if '\x00' in text_payload:
                is_binary = True
                text_payload = "[Binary Data Captured]"
        except UnicodeDecodeError:
            is_binary = True
            text_payload = "[Binary Data Captured]"
            
        base64_payload = base64.b64encode(payload_bytes).decode('utf-8')
        
        return {
            "payload": text_payload,
            "is_binary": is_binary,
            "base64": base64_payload
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
