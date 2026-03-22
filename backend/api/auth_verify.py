import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.compute.auth import verify_image

router = APIRouter()


class VerifyRequest(BaseModel):
    file_path: str


@router.post("/api/auth/verify")
async def verify_authenticity(request: VerifyRequest):
    """
    Verify whether an image was signed by StegXtreme
    and has not been modified since signing.
    """
    if not os.path.exists(request.file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.file_path}"
        )

    result = verify_image(request.file_path)

    return {
        "is_authentic"         : result.is_authentic,
        "verdict"              : result.verdict,
        "verdict_color"        : result.verdict_color,
        "signed_at"            : result.signed_at,
        "key_fingerprint"      : result.key_fingerprint,
        "modification_detected": result.modification_detected,
        "error"                : result.error
    }