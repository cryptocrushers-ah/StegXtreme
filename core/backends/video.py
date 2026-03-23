"""
video.py — DWT Spread-Spectrum Video Steganography Backend
==========================================================
Wraps the optimised video_stego.py DWT-SS engine so the rest of the
project uses the same VideoBackend interface as Image/Audio backends.

Supported algorithms (passed as `algorithm` parameter):
  "dwt_ss"  (default)  — DWT Spread Spectrum + ECC + AES-256-GCM
  "lsb"                — spatial LSB across frames (legacy, no ECC)

Output is always lossless HuffYUV (.avi).  The caller must handle the
filename change (.mp4 → .avi) if needed.
"""

import os
import numpy as np
import cv2
import struct
import logging

from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

# ── Import the DWT-SS engine — multiple fallback paths ───────────────
_DWT_AVAILABLE = False
_dwt_embed = None
_dwt_extract = None

def _try_import_video_stego():
    global _dwt_embed, _dwt_extract, _DWT_AVAILABLE
    import importlib, sys

    # Strategy 1: package import (server runs from project root)
    try:
        mod = importlib.import_module('core.backends.video_stego')
        _dwt_embed   = mod.embed
        _dwt_extract = mod.extract
        _DWT_AVAILABLE = True
        return
    except ImportError:
        pass

    # Strategy 2: load directly by file path (handles odd working dirs)
    try:
        import importlib.util, pathlib
        here = pathlib.Path(__file__).parent / 'video_stego.py'
        spec = importlib.util.spec_from_file_location('video_stego', here)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _dwt_embed   = mod.embed
        _dwt_extract = mod.extract
        _DWT_AVAILABLE = True
    except Exception as e:
        logging.error("Failed to import video_stego", exc_info=True)
        _DWT_AVAILABLE = False

_try_import_video_stego()

# _SALT dynamically generated in embed


class VideoBackend:
    # ------------------------------------------------------------------ embed
    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload: bytes,
              password: str, algorithm: str = "dwt_ss") -> str:
        if algorithm in ("dwt_ss", "default", ""):
            return cls._embed_dwt(cover_path, out_path, payload, password)
        elif algorithm == "lsb":
            return cls._embed_lsb(cover_path, out_path, payload, password)
        else:
            # Unknown algorithm — fall through to DWT
            return cls._embed_dwt(cover_path, out_path, payload, password)

    # ------------------------------------------------------------------ extract
    @classmethod
    def extract(cls, stego_path: str, password: str,
                algorithm: str = "dwt_ss") -> bytes:
        if algorithm in ("dwt_ss", "default", ""):
            return cls._extract_dwt(stego_path, password)
        elif algorithm == "lsb":
            return cls._extract_lsb(stego_path, password)
        else:
            return cls._extract_dwt(stego_path, password)

    # ══════════════════════════════════════════════════════════════════
    #  DWT-SS path (preferred)
    # ══════════════════════════════════════════════════════════════════
    @classmethod
    def _embed_dwt(cls, cover_path: str, out_path: str,
                   payload: bytes, password: str) -> str:
        if not _DWT_AVAILABLE:
            raise ImportError(
                "video_stego.py not found. Place it at core/backends/video_stego.py"
            )
        # video_stego.embed expects text or image_path; we encode bytes as text
        # via latin-1 to preserve every byte value, then wrap it back on extract.
        # We pass a custom raw-bytes marker so extract() knows to decode correctly.
        import tempfile, shutil

        # Ensure output is .avi
        if not out_path.lower().endswith('.avi'):
            out_path = os.path.splitext(out_path)[0] + '.avi'

        # Encode raw bytes as latin-1 text with a sentinel prefix
        SENTINEL = "\x00\x01RAW\x01\x00"
        text_payload = SENTINEL + payload.decode('latin-1')

        result = _dwt_embed(
            video_in=cover_path,
            video_out=out_path,
            text=text_payload,
            password=password,
        )
        return result

    @classmethod
    def _extract_dwt(cls, stego_path: str, password: str) -> bytes:
        if not _DWT_AVAILABLE:
            raise ImportError(
                "video_stego.py not found. Place it at core/backends/video_stego.py"
            )
        SENTINEL = "\x00\x01RAW\x01\x00"
        result = _dwt_extract(video_in=stego_path, password=password)

        if isinstance(result, str):
            if result.startswith(SENTINEL):
                return result[len(SENTINEL):].encode('latin-1')
            return result.encode('utf-8')
        elif isinstance(result, bytes):
            return result
        else:
            return str(result).encode('utf-8')

    # ══════════════════════════════════════════════════════════════════
    #  Legacy LSB path
    # ══════════════════════════════════════════════════════════════════
    @classmethod
    def _embed_lsb(cls, cover_path: str, out_path: str,
                   payload: bytes, password: str) -> str:
        if not out_path.lower().endswith('.avi'):
            out_path = os.path.splitext(out_path)[0] + '.avi'

        cap = cv2.VideoCapture(cover_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {cover_path}")

        fps    = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Encrypt
        salt = os.urandom(16)
        key = derive_key(password, salt)
        encrypted = salt + aes_encrypt(payload, key)

        bits = np.unpackbits(np.frombuffer(encrypted, dtype=np.uint8))
        # 32-bit big-endian bit-count header
        length_bits = np.unpackbits(np.array([len(bits)], dtype='>u4').view(np.uint8))
        all_bits = np.concatenate([length_bits, bits])

        max_cap = width * height * 3 * total_frames
        if len(all_bits) > max_cap:
            raise ValueError(
                f"Payload too large for LSB: need {len(all_bits)} bits, "
                f"capacity {max_cap} bits."
            )

        fourcc = cv2.VideoWriter_fourcc(*'HFYU')
        out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        if not out.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
            if not out.isOpened():
                cap.release()
                raise ValueError("Cannot open video writer (need HFYU or FFV1 codec).")

        bit_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if bit_idx < len(all_bits):
                flat = frame.flatten().astype(np.int32)
                n = min(len(flat), len(all_bits) - bit_idx)
                flat[:n] = (flat[:n] & 0xFE) | all_bits[bit_idx:bit_idx + n].astype(np.int32)
                bit_idx += n
                frame = flat.astype(np.uint8).reshape(frame.shape)
            out.write(frame)

        cap.release()
        out.release()
        
        if bit_idx < len(all_bits):
            raise ValueError(f"Payload truncated: video frames ended before payload finished. Wrote {bit_idx} of {len(all_bits)} bits.")
            
        return out_path

    @classmethod
    def _extract_lsb(cls, stego_path: str, password: str) -> bytes:
        cap = cv2.VideoCapture(stego_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open stego video: {stego_path}")

        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Read 32-bit header first
        header_bits: list[int] = []
        while len(header_bits) < 32:
            ret, frame = cap.read()
            if not ret:
                break
            flat = frame.flatten()
            n = min(len(flat), 32 - len(header_bits))
            header_bits.extend((flat[:n] & 1).tolist())

        if len(header_bits) < 32:
            cap.release()
            raise ValueError("Failed to read length header from video.")

        payload_len = int(np.frombuffer(
            np.packbits(np.array(header_bits, dtype=np.uint8)), dtype='>u4')[0])
        total_bits = 32 + payload_len

        all_bits = np.zeros(total_bits, dtype=np.uint8)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        bit_idx = 0
        while bit_idx < total_bits:
            ret, frame = cap.read()
            if not ret:
                break
            flat = frame.flatten()
            n = min(len(flat), total_bits - bit_idx)
            all_bits[bit_idx:bit_idx + n] = flat[:n] & 1
            bit_idx += n

        cap.release()

        if bit_idx < total_bits:
            raise ValueError("Video file truncated — could not read full payload.")

        full_encrypted = np.packbits(all_bits[32:]).tobytes()
        if len(full_encrypted) < 16:
            raise ValueError("Payload too short to contain salt.")
        salt = full_encrypted[:16]
        encrypted = full_encrypted[16:]
        key = derive_key(password, salt)
        try:
            return aes_decrypt(encrypted, key)
        except Exception as exc:
            raise ValueError(
                "Decryption failed — wrong password or video re-encoded (lossy)."
            ) from exc
