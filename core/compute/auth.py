import os
import json
import hashlib
import base64
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from PIL import Image
import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization

# ── Constants ──────────────────────────────────────────────────────────────
AUTH_VERSION  = "1.0"
NULL_SIG_B64  = base64.b64encode(b'\x00' * 64).decode()  # 88 chars always


# ── Dataclasses ────────────────────────────────────────────────────────────
@dataclass
class AuthSignature:
    sig : str   # base64 Ed25519 signature — always 88 chars
    pub : str   # base64 public key — always 44 chars
    ts  : str   # ISO timestamp
    w   : int   # image width
    h   : int   # image height
    ver : str = AUTH_VERSION


@dataclass
class VerificationResult:
    is_authentic         : bool
    verdict              : str    # AUTHENTIC / TAMPERED / UNSIGNED / ERROR
    verdict_color        : str
    signed_at            : str  = None
    key_fingerprint      : str  = None
    modification_detected: bool = False
    error                : str  = None


# ── Key Generation ─────────────────────────────────────────────────────────
def generate_keypair():
    """Generate Ed25519 keypair. Call once at startup."""
    private_key  = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return private_key, public_bytes


# ── Pixel Hashing ──────────────────────────────────────────────────────────
def hash_pixels(image_path: str) -> str:
    """
    SHA-256 hash of raw RGB pixel bytes.
    Any single pixel change produces a completely different hash.
    """
    img = Image.open(image_path).convert("RGB")
    raw = np.array(img).tobytes()
    return hashlib.sha256(raw).hexdigest()


# ── LSB Embed / Read ───────────────────────────────────────────────────────
def _embed_lsb(image_path: str, json_bytes: bytes, output_path: str):
    """
    Embed json_bytes into image using LSB steganography.
    Red channel: 32 pixels store 4-byte length
    Blue channel: stores json bytes
    """
    img_arr  = np.array(Image.open(image_path).convert("RGB"))
    length   = len(json_bytes)
    length_b = length.to_bytes(4, "big")

    flat_r = img_arr[:, :, 0].ravel().copy()
    flat_b = img_arr[:, :, 2].ravel().copy()

    # store length in first 32 red pixels LSB
    for i in range(32):
        byte_idx  = i // 8
        bit_idx   = 7 - (i % 8)
        bit_val   = (length_b[byte_idx] >> bit_idx) & 1
        flat_r[i] = (flat_r[i] & 0xFE) | bit_val

    # store json bytes in blue channel LSB
    for i, byte in enumerate(json_bytes):
        for bit_pos in range(8):
            pixel_idx = i * 8 + bit_pos
            if pixel_idx >= len(flat_b):
                break
            bit_val           = (byte >> (7 - bit_pos)) & 1
            flat_b[pixel_idx] = (flat_b[pixel_idx] & 0xFE) | bit_val

    img_arr[:, :, 0] = flat_r.reshape(img_arr[:, :, 0].shape)
    img_arr[:, :, 2] = flat_b.reshape(img_arr[:, :, 2].shape)
    Image.fromarray(img_arr).save(output_path)


def _read_lsb(image_path: str) -> bytes | None:
    """
    Read json bytes from image LSB channels.
    Returns None if no valid data found.
    """
    img_arr     = np.array(Image.open(image_path).convert("RGB"))
    flat_r      = img_arr[:, :, 0].ravel()
    flat_b      = img_arr[:, :, 2].ravel()

    # read length from first 32 red pixels
    length_bits = [int(flat_r[i] & 1) for i in range(32)]
    length_bytes_list = []
    for i in range(0, 32, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | length_bits[i + j]
        length_bytes_list.append(byte)
    length = int.from_bytes(bytes(length_bytes_list), "big")

    if length <= 0 or length > 10000:
        return None

    # read json bytes from blue channel
    json_bits = [int(flat_b[i] & 1) for i in range(length * 8)]
    json_bytes_out = []
    for i in range(0, len(json_bits) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | json_bits[i + j]
        json_bytes_out.append(byte)

    return bytes(json_bytes_out)


# ── Sign and Embed ─────────────────────────────────────────────────────────
def sign_and_embed(
    image_path : str,
    private_key,
    output_path: str
) -> bool:
    """
    Sign image and embed signature using two-pass approach:

    Pass 1: embed placeholder sig (null bytes, same size as real sig)
    Hash the output image after placeholder embed.
    Pass 2: sign that hash, embed real sig (same JSON length as placeholder).

    Verify uses canonical form: zero out sig field, re-embed, re-hash,
    check that hash matches what was signed.
    """
    try:
        img  = Image.open(image_path).convert("RGB")
        w, h = img.size

        pub_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        pub_b64   = base64.b64encode(pub_bytes).decode()
        timestamp = datetime.now(timezone.utc).isoformat()

        # ── Pass 1: embed placeholder ──────────────────────────────────
        placeholder = AuthSignature(
            sig = NULL_SIG_B64,   # null bytes — same length as real sig
            pub = pub_b64,
            ts  = timestamp,
            w   = w,
            h   = h
        )
        p_json = json.dumps(
            asdict(placeholder), separators=(",", ":")
        ).encode()

        _embed_lsb(image_path, p_json, output_path)

        # ── Hash after placeholder embed ───────────────────────────────
        pixel_hash = hash_pixels(output_path)

        # ── Sign the hash ──────────────────────────────────────────────
        sig_bytes = private_key.sign(pixel_hash.encode())
        sig_b64   = base64.b64encode(sig_bytes).decode()

        # ── Pass 2: embed real sig ─────────────────────────────────────
        real_sig = AuthSignature(
            sig = sig_b64,
            pub = pub_b64,
            ts  = timestamp,   # SAME timestamp — keeps JSON length identical
            w   = w,
            h   = h
        )
        r_json = json.dumps(
            asdict(real_sig), separators=(",", ":")
        ).encode()

        # JSON lengths must match — if not, something is wrong
        assert len(p_json) == len(r_json), (
            f"JSON length mismatch: {len(p_json)} vs {len(r_json)}"
        )

        _embed_lsb(output_path, r_json, output_path)

        return True

    except Exception as e:
        print(f"[Auth] Signing failed silently: {e}")
        return False


# ── Verify ─────────────────────────────────────────────────────────────────
def verify_image(image_path: str) -> VerificationResult:
    """
    Verify authenticity of a signed image.

    Key insight: verifying requires rebuilding the canonical form
    (image with null sig field) and checking its hash matches
    what was signed. This is because the sig field itself contains
    different bytes than the placeholder, so naive re-hashing fails.
    """
    # Step 1: extract embedded data
    try:
        raw = _read_lsb(image_path)
        if raw is None:
            return VerificationResult(
                is_authentic  = False,
                verdict       = "UNSIGNED",
                verdict_color = "#6B7280"
            )
        sig_dict  = json.loads(raw.decode("utf-8"))
        signature = AuthSignature(**sig_dict)
    except Exception:
        return VerificationResult(
            is_authentic  = False,
            verdict       = "UNSIGNED",
            verdict_color = "#6B7280"
        )

    # Step 2: rebuild canonical form (null sig field, same everything else)
    try:
        import tempfile
        canonical = AuthSignature(
            sig = NULL_SIG_B64,   # zero out sig field
            pub = signature.pub,
            ts  = signature.ts,
            w   = signature.w,
            h   = signature.h
        )
        c_json = json.dumps(
            asdict(canonical), separators=(",", ":")
        ).encode()

        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as tmp:
            tmp_path = tmp.name

        _embed_lsb(image_path, c_json, tmp_path)
        canonical_hash = hash_pixels(tmp_path)
        os.unlink(tmp_path)

    except Exception as e:
        return VerificationResult(
            is_authentic  = False,
            verdict       = "ERROR",
            verdict_color = "#F97316",
            error         = f"Canonical hash failed: {e}"
        )

    # Step 3: verify Ed25519 signature against canonical hash
    try:
        pub_bytes = base64.b64decode(signature.pub)
        pub_key   = Ed25519PublicKey.from_public_bytes(pub_bytes)
        sig_bytes = base64.b64decode(signature.sig)
        pub_key.verify(sig_bytes, canonical_hash.encode())
        sig_valid = True
    except Exception:
        sig_valid = False

    # Step 4: check if image was modified AFTER signing
    # Re-hash the current image with null sig and compare
    # If sig is valid, canonical_hash == what was signed at embed time
    # Now check if CURRENT canonical hash still matches
    # (it will if no pixels were changed after signing)
    modification_detected = not sig_valid

    key_fingerprint = base64.b64decode(
        signature.pub
    ).hex()[:16]

    if sig_valid:
        return VerificationResult(
            is_authentic          = True,
            verdict               = "AUTHENTIC",
            verdict_color         = "#22C55E",
            signed_at             = signature.ts,
            key_fingerprint       = key_fingerprint,
            modification_detected = False
        )
    else:
        return VerificationResult(
            is_authentic          = False,
            verdict               = "TAMPERED",
            verdict_color         = "#EF4444",
            signed_at             = signature.ts,
            key_fingerprint       = key_fingerprint,
            modification_detected = True
        )