"""
embed.py — /api/embed endpoint
===============================
Fixes:
  • Output filename uses actual backend output path (video DWT → .avi)
  • Download filename reflects real extension
  • Unique temp IDs prevent collisions on concurrent requests
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil, os, uuid, logging

from core.backends.router import get_backend
from backend.utils.validation import validate_file

router = APIRouter()

TEMP_DIR = "storage/temp"
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/api/embed")
async def embed_data(
    file: UploadFile = File(...),
    text_payload: str  = Form(None),
    file_payload: UploadFile = File(None),
    password: str      = Form(...),
    algorithm: str     = Form("dct"),
):
    await validate_file(file)

    try:
        # ── payload bytes ────────────────────────────────────────────
        if file_payload:
            payload_bytes = await file_payload.read()
            if not payload_bytes:
                raise ValueError("File payload is empty.")
        elif text_payload:
            payload_bytes = text_payload.encode("utf-8")
        else:
            raise ValueError("No payload provided — supply text or a file.")

        # ── save carrier to temp ─────────────────────────────────────
        original_ext = os.path.splitext(file.filename or "file")[-1].lstrip(".")
        unique_id    = str(uuid.uuid4())
        in_path      = os.path.join(TEMP_DIR, f"{unique_id}_in.{original_ext}")
        # out_path is a suggestion; DWT video will rename to .avi
        out_path     = os.path.join(TEMP_DIR, f"{unique_id}_stego.{original_ext}")

        with open(in_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # ── run backend ──────────────────────────────────────────────
        BackendClass = get_backend(in_path)
        actual_out = BackendClass.embed(
            cover_path=in_path,
            out_path=out_path,
            payload=payload_bytes,
            password=password,
            algorithm=algorithm,
        )

        # actual_out may differ from out_path (e.g. .mp4 → .avi)
        if not os.path.exists(actual_out):
            raise RuntimeError(f"Backend did not produce output file: {actual_out}")

        # ── neural feedback (best-effort) ────────────────────────────
        try:
            # Neural feedback bypassed to prevent PyTorch CUDA locks
            # from backend.api.deps import feedback_engine
            # feedback_engine.evaluate_file(actual_out)
            pass
        except Exception as fb_err:
            logging.error(f"[embed] Feedback skipped: {fb_err}", exc_info=True)

        # ── build download filename ──────────────────────────────────
        base     = os.path.splitext(file.filename or "stego")[0]
        real_ext = os.path.splitext(actual_out)[-1]          # e.g. ".avi"
        dl_name  = f"{base}_stego{real_ext}"

        return FileResponse(
            actual_out,
            media_type="application/octet-stream",
            filename=dl_name,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))
