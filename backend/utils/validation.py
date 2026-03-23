from typing import Optional
from fastapi import UploadFile, HTTPException
import magic

MAX_FILE_SIZE = 50000 * 1024 * 1024  # 50GB, effectively removed

ALLOWED_MIME_TYPES = {
    "image": ["image/png", "image/jpeg", "image/bmp"],
    "audio": ["audio/wav", "audio/mpeg", "audio/x-wav"],
    "video": ["video/mp4", "video/x-msvideo", "video/quicktime"]
}

async def validate_file(file: UploadFile, expected_category: Optional[str] = None):
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Check MIME type
    header = file.file.read(2048)
    file.file.seek(0)
    mime = magic.from_buffer(header, mime=True)
    
    if expected_category:
        allowed = ALLOWED_MIME_TYPES.get(expected_category, [])
        if mime not in allowed:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {mime}. Expected {expected_category} ({', '.join(allowed)})"
            )
    else:
        all_allowed = [m for cat in ALLOWED_MIME_TYPES.values() for m in cat]
        if mime not in all_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or unsupported file type: {mime}. Expected an image, audio, or video file."
            )
    
    return mime
