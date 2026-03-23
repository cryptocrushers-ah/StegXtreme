"""
image.py — LSB & DCT Image Steganography Backend
=================================================
Fixes applied:
  • sign_and_embed() called AFTER the file is written (not before)
  • "default" algorithm mapped explicitly to "dct"
  • Duplicate imports removed
  • _from_bits() pads to byte-boundary before packbits
"""

import cv2
import numpy as np
import os
import logging

from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt
from core.compute.auth import sign_and_embed, generate_keypair

# Temporary session key for 1st round presentation
_S_PRI, _S_PUB = generate_keypair()

# _SALT dynamically generated in embed


class ImageBackend:
    # Mid-frequency DCT coefficients (zig-zag mid-band)
    DCT_COEFFS = [(4,4),(3,4),(4,3),(3,3),(5,5),(5,4),(4,5),(2,5),(5,2)]

    # ── bit helpers ──────────────────────────────────────────────────
    @classmethod
    def _to_bits(cls, data: bytes) -> np.ndarray:
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

    @classmethod
    def _from_bits(cls, bits: np.ndarray) -> bytes:
        bits = np.asarray(bits, dtype=np.uint8)
        pad = (8 - len(bits) % 8) % 8
        if pad:
            bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
        return np.packbits(bits).tobytes()

    # ── public embed ─────────────────────────────────────────────────
    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload: bytes,
              password: str, algorithm: str = "dct") -> str:
        img = cv2.imread(cover_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot open image: {cover_path}")

        salt = os.urandom(16)
        key = derive_key(password, salt)
        encrypted = salt + aes_encrypt(payload, key)

        payload_bits    = cls._to_bits(encrypted)
        payload_bit_len = len(payload_bits)

        length_bytes = np.array([payload_bit_len], dtype='>u4').view(np.uint8)
        all_bits = np.concatenate([
            cls._to_bits(bytes(length_bytes)),
            payload_bits
        ])

        # Map "default" → "dct" so auto-select always resolves
        algo = algorithm.lower() if algorithm else "dct"
        if algo in ("default", ""):
            algo = "dct"

        # Force lossless output to prevent compression from destroying the payload
        if not out_path.lower().endswith('.png') and not out_path.lower().endswith('.bmp'):
            out_path = os.path.splitext(out_path)[0] + '.png'

        if algo == "lsb":
            result = cls._embed_lsb(img, out_path, all_bits)
        else:  # dct (and any unknown value)
            result = cls._embed_dct(img, out_path, all_bits)

        # Re-enabled for DCT: LSB signature is small enough that it doesn't 
        # interfere with mid-frequency DCT coefficients, though it breaks 
        # pure LSB steganography.
        if algo != "lsb":
            sign_and_embed(out_path, _S_PRI, out_path)
            
        return result

    # ── public extract ───────────────────────────────────────────────
    @classmethod
    def extract(cls, stego_path: str, password: str,
                algorithm: str = "dct") -> bytes:
        img = cv2.imread(stego_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot open stego image: {stego_path}")

        algo = algorithm.lower() if algorithm else "dct"
        if algo in ("default", ""):
            algo = "dct"

        def get_bits(count: int):
            if algo == "lsb":
                return cls._extract_lsb_bits(img, count)
            return cls._extract_dct_bits(img, count)

        header = np.array(get_bits(32), dtype=np.uint8)
        if len(header) < 32:
            raise ValueError("Could not read length header — wrong algorithm or corrupt file.")

        payload_len = int(np.frombuffer(cls._from_bits(header)[:4], dtype='>u4')[0])

        if payload_len == 0 or payload_len > 200_000_000:
            raise ValueError(
                "Invalid payload length decoded — wrong password or algorithm mismatch."
            )

        total = 32 + payload_len
        all_bits = np.array(get_bits(total), dtype=np.uint8)
        if len(all_bits) < total:
            raise ValueError(
                f"Extracted only {len(all_bits)} bits, need {total}. "
                "Wrong algorithm or image re-compressed."
            )

        full_encrypted = cls._from_bits(all_bits[32:32 + payload_len])
        if len(full_encrypted) < 16:
            raise ValueError("Payload too short to contain salt.")
        salt = full_encrypted[:16]
        encrypted = full_encrypted[16:]
        key = derive_key(password, salt)
        try:
            return aes_decrypt(encrypted, key)
        except Exception as exc:
            raise ValueError(
                "Decryption failed — wrong password or algorithm mismatch."
            ) from exc

    # ── LSB embed / extract ──────────────────────────────────────────
    @classmethod
    def _embed_lsb(cls, img: np.ndarray, out_path: str,
                   all_bits: np.ndarray) -> str:
        h, w, c = img.shape
        if len(all_bits) > h * w * c:
            raise ValueError(
                f"Payload too large for LSB: need {len(all_bits)} bits, "
                f"capacity {h * w * c}."
            )
        flat = img.flatten().copy()
        n = len(all_bits)
        flat[:n] = (flat[:n] & np.uint8(0xFE)) | all_bits[:n].astype(np.uint8)
        cv2.imwrite(out_path, flat.reshape(img.shape))
        return out_path

    @classmethod
    def _extract_lsb_bits(cls, img: np.ndarray, count: int) -> list:
        flat = img.flatten()
        if len(flat) < count:
            raise ValueError(f"Image too small for LSB extraction of {count} bits.")
        return (flat[:count] & 1).tolist()

    # ── DCT embed / extract ──────────────────────────────────────────
    @classmethod
    def _embed_dct(cls, img: np.ndarray, out_path: str,
                   all_bits: np.ndarray) -> str:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        Q = 10.0
        coeffs = cls.DCT_COEFFS

        h, w = ycrcb.shape[:2]
        h_pad = h + (8 - h % 8) % 8
        w_pad = w + (8 - w % 8) % 8
        bh, bw = h_pad // 8, w_pad // 8

        max_cap = bh * bw * 3 * len(coeffs)
        if len(all_bits) > max_cap:
            raise ValueError(
                f"Payload too large for DCT: need {len(all_bits)} bits, "
                f"capacity {max_cap}."
            )

        bit_idx = 0
        for ch in range(3):
            channel = ycrcb[:, :, ch].astype(np.float32)
            padded  = np.zeros((h_pad, w_pad), dtype=np.float32)
            padded[:h, :w] = channel

            for i in range(bh):
                if bit_idx >= len(all_bits): break
                for j in range(bw):
                    if bit_idx >= len(all_bits): break
                    block     = padded[i*8:(i+1)*8, j*8:(j+1)*8]
                    dct_block = cv2.dct(block)
                    for row, col in coeffs:
                        if bit_idx >= len(all_bits): break
                        val = round(dct_block[row, col] / Q)
                        if val % 2 != int(all_bits[bit_idx]):
                            val += 1 if all_bits[bit_idx] == 1 else -1
                        dct_block[row, col] = val * Q
                        bit_idx += 1
                    padded[i*8:(i+1)*8, j*8:(j+1)*8] = cv2.idct(dct_block)

            ycrcb[:, :, ch] = np.clip(padded[:h, :w], 0, 255).astype(np.uint8)

        cv2.imwrite(out_path, cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR))
        return out_path

    @classmethod
    def _extract_dct_bits(cls, img: np.ndarray, count: int) -> list:
        ycrcb  = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        h, w   = ycrcb.shape[:2]
        h_pad  = h + (8 - h % 8) % 8
        w_pad  = w + (8 - w % 8) % 8
        bh, bw = h_pad // 8, w_pad // 8
        Q      = 10.0
        coeffs = cls.DCT_COEFFS
        bits: list[int] = []

        for ch in range(3):
            channel = ycrcb[:, :, ch].astype(np.float32)
            padded  = np.zeros((h_pad, w_pad), dtype=np.float32)
            padded[:h, :w] = channel

            for i in range(bh):
                for j in range(bw):
                    block     = padded[i*8:(i+1)*8, j*8:(j+1)*8]
                    dct_block = cv2.dct(block)
                    for r, c in coeffs:
                        bits.append(abs(int(round(dct_block[r, c] / Q))) % 2)
                        if len(bits) >= count:
                            return bits
        return bits
