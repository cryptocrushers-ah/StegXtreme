from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
import uuid
from core.backends.router import get_backend
from backend.utils.validation import validate_file

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/api/embed")
async def embed_data(
    file: UploadFile = File(...),
    text_payload: str = Form(None),
    file_payload: UploadFile = File(None),
    password: str = Form(...),
    algorithm: str = Form("default")
):
    await validate_file(file)
    try:
        # Get payload bytes
        if file_payload:
            payload_bytes = await file_payload.read()
            if not payload_bytes:
                 raise ValueError("File payload is empty.")
        elif text_payload:
            payload_bytes = text_payload.encode('utf-8')
        else:
            raise ValueError("No payload provided. Please provide text or a file.")
        # Save uploaded file
        ext = file.filename.split('.')[-1]
        unique_id = str(uuid.uuid4())
        in_path = os.path.join(TEMP_DIR, f"{unique_id}_in.{ext}")
        out_path = os.path.join(TEMP_DIR, f"{unique_id}_stego.{ext}")
        
        with open(in_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get appropriate backend
        BackendClass = get_backend(in_path)
        
        # Embed payload
        BackendClass.embed(
            cover_path=in_path,
            out_path=out_path,
            payload=payload_bytes,
            password=password,
            algorithm=algorithm
        )

        # Neural Feedback Loop
        try:
            from backend.api.deps import feedback_engine
            feedback_engine.evaluate_file(out_path)
        except Exception as e:
            print(f"Feedback trigger failed: {e}")
        
        # Return the modified file
        return FileResponse(out_path, media_type="application/octet-stream", filename=f"stego_{file.filename}")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
