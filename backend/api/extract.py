"""
extract.py — /api/extract endpoint
====================================
Fixes:
  • Uses unique ID for temp path (prevents collision)
  • Passes algorithm straight to backend (no "default" ambiguity)
  • Returns clean JSON with text / binary / base64
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.utils.validation import validate_file
import os, uuid, base64, shutil


from core.backends.router import get_backend

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_SIZE = 50000 * 1024 * 1024   # 50 GB


@router.post("/api/extract")
async def extract_data(
    file: UploadFile = File(...),
    password: str    = Form(...),
    algorithm: str   = Form("dct"),
):
    await validate_file(file)
    # size guard check is offloaded to validation.py now
    ext       = os.path.splitext(file.filename or "file")[-1].lstrip(".")
    unique_id = str(uuid.uuid4())
    in_path   = os.path.join(TEMP_DIR, f"{unique_id}_extract.{ext}")

    try:
        with open(in_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        BackendClass   = get_backend(in_path)
        payload_bytes  = BackendClass.extract(
            stego_path=in_path,
            password=password,
            algorithm=algorithm,
        )

        # ── attempt UTF-8 decode ─────────────────────────────────────
        is_binary    = False
        text_payload = ""
        try:
            text_payload = payload_bytes.decode("utf-8")
            if "\x00" in text_payload:
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "null byte")
        except (UnicodeDecodeError, ValueError):
            is_binary    = True
            text_payload = "[Binary payload — use Download to save the file]"

        return {
            "payload":   text_payload,
            "is_binary": is_binary,
            "base64":    base64.b64encode(payload_bytes).decode("utf-8"),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        try:
            os.remove(in_path)
        except OSError:
            pass
