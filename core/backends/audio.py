"""
audio.py — LSB Audio Steganography Backend (fixed)
===================================================
Root cause of previous bugs:
  • Float → int32 → mask → float → write → read → float → int32 chain
    corrupts samples at -32768 boundary: (-32768 & 0xFFFE as int32) = +32768
    which is out of int16 range, so sf.write clips it silently, destroying bits.

Fix: read and write audio directly as int16 — zero float conversion, zero
     clipping, zero round-trip error.  sf.read/write both support dtype='int16'.

Header: 4 bytes (32 bits) big-endian uint32 = number of BYTES in encrypted payload.
"""

import numpy as np
import soundfile as sf
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

import os
# _SALT dynamically generated in embed


class AudioBackend:

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _to_bits(data: bytes) -> np.ndarray:
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

    @staticmethod
    def _from_bits(bits: np.ndarray) -> bytes:
        bits = np.asarray(bits, dtype=np.uint8)
        pad = (8 - len(bits) % 8) % 8
        if pad:
            bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
        return np.packbits(bits).tobytes()

    # ── embed ─────────────────────────────────────────────────────────
    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload: bytes,
              password: str, algorithm: str = "lsb") -> str:
        # Read directly as int16 — no float, no clipping
        data, samplerate = sf.read(cover_path, dtype='int16', always_2d=False)

        salt = os.urandom(16)
        key = derive_key(password, salt)
        encrypted = salt + aes_encrypt(payload, key)

        # Header = 4-byte big-endian length of encrypted payload (byte count)
        header = np.array([len(encrypted)], dtype='>u4').view(np.uint8)
        all_bits = np.concatenate([
            cls._to_bits(bytes(header)),   # 32 bits
            cls._to_bits(encrypted),       # payload bits
        ]).astype(np.int16)

        flat = data.flatten().copy()

        if len(all_bits) > len(flat):
            raise ValueError(
                f"Payload too large: need {len(all_bits)} samples, "
                f"audio has {len(flat)}."
            )

        # LSB embed in pure int16 — safe: -2 as int16 = 0xFFFE, masks bottom bit
        flat[:len(all_bits)] = (flat[:len(all_bits)] & np.int16(-2)) | all_bits

        sf.write(out_path, flat.reshape(data.shape), samplerate, subtype='PCM_16')
        return out_path

    # ── extract ───────────────────────────────────────────────────────
    @classmethod
    def extract(cls, stego_path: str, password: str,
                algorithm: str = "lsb") -> bytes:
        data, _ = sf.read(stego_path, dtype='int16', always_2d=False)
        flat = data.flatten()

        if len(flat) < 32:
            raise ValueError("Audio file too short to contain a header.")

        # Read 32-bit header → encrypted byte count
        header_bits = (flat[:32] & 1).astype(np.uint8)
        enc_len = int(np.frombuffer(cls._from_bits(header_bits)[:4], dtype='>u4')[0])

        if enc_len == 0 or enc_len > 200_000_000:
            raise ValueError(
                f"Invalid header length {enc_len} — wrong password or not a stego file."
            )

        total_bits = 32 + enc_len * 8
        if len(flat) < total_bits:
            raise ValueError(
                f"Audio too short: need {total_bits} samples, have {len(flat)}."
            )

        payload_bits = (flat[32:total_bits] & 1).astype(np.uint8)
        full_encrypted = cls._from_bits(payload_bits)[:enc_len]
        if len(full_encrypted) < 16:
            raise ValueError("Payload too short to contain salt.")
        salt = full_encrypted[:16]
        encrypted = full_encrypted[16:]

        key = derive_key(password, salt)
        try:
            return aes_decrypt(encrypted, key)
        except Exception as exc:
            raise ValueError(
                "Decryption failed — wrong password or corrupted audio."
            ) from exc
