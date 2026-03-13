import cv2
import numpy as np
import os
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

class ImageBackend:
    # A basic block-based DCT approach
    # We embed bits into the mid-frequency coefficient of the 8x8 DCT block of the Y channel.

    @classmethod
    def _to_bits(cls, data: bytes) -> np.ndarray:
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

    @classmethod
    def _from_bits(cls, bits: np.ndarray) -> bytes:
        return np.packbits(bits).tobytes()

    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload: bytes, password: str) -> str:
        img = cv2.imread(cover_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot open image: {cover_path}")

        salt = b'StegXtreme_Image'
        key = derive_key(password, salt)
        
        # Encrypt payload
        encrypted_payload = aes_encrypt(payload, key)
        
        # Create full payload: length (32 bits) + data
        payload_len = len(encrypted_payload)
        length_bytes = np.array([payload_len], dtype='>u4').view(np.uint8)
        
        all_bits = np.concatenate((
            cls._to_bits(length_bytes.tobytes()),
            cls._to_bits(encrypted_payload)
        ))

        # Convert to YCrCb
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb[:, :, 0].astype(np.float32)

        # Ensure image dimensions are a multiple of 8
        h, w = y_channel.shape
        h_pad = h + (8 - h % 8) % 8
        w_pad = w + (8 - w % 8) % 8
        
        # Padding
        if h_pad != h or w_pad != w:
             padded_y = np.zeros((h_pad, w_pad), dtype=np.float32)
             padded_y[:h, :w] = y_channel
        else:
             padded_y = y_channel.copy()

        # DCT Embedding parameters
        Q = 10.0 # Quantization step for embedding

        blocks_h, blocks_w = h_pad // 8, w_pad // 8
        max_capacity = blocks_h * blocks_w

        if len(all_bits) > max_capacity:
            raise ValueError(f"Payload too large. Max capacity is {max_capacity} bits, payload is {len(all_bits)} bits.")

        bit_idx = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                if bit_idx >= len(all_bits):
                    break
                
                block = padded_y[i*8:(i+1)*8, j*8:(j+1)*8]
                dct_block = cv2.dct(block)
                
                # Embed in mid-frequency e.g. (4, 4)
                coeff = dct_block[4, 4]
                val = round(coeff / Q)
                bit = all_bits[bit_idx]
                
                if val % 2 != bit:
                    if bit == 1:
                        val += 1
                    else:
                        val -= 1
                
                dct_block[4, 4] = val * Q
                
                padded_y[i*8:(i+1)*8, j*8:(j+1)*8] = cv2.idct(dct_block)
                bit_idx += 1

        # Truncate to original size
        ycrcb[:, :, 0] = np.clip(padded_y[:h, :w], 0, 255).astype(np.uint8)
        
        # Back to BGR
        stego_img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        cv2.imwrite(out_path, stego_img)
        
        return out_path

    @classmethod
    def extract(cls, stego_path: str, password: str) -> bytes:
        img = cv2.imread(stego_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot open stego image: {stego_path}")

        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb[:, :, 0].astype(np.float32)

        h, w = y_channel.shape
        h_pad = h + (8 - h % 8) % 8
        w_pad = w + (8 - w % 8) % 8
        
        if h_pad != h or w_pad != w:
             padded_y = np.zeros((h_pad, w_pad), dtype=np.float32)
             padded_y[:h, :w] = y_channel
        else:
             padded_y = y_channel

        Q = 10.0
        blocks_h, blocks_w = h_pad // 8, w_pad // 8
        
        extracted_bits = []
        
        # First read the 32-bit length
        for i in range(blocks_h):
            for j in range(blocks_w):
                if len(extracted_bits) >= 32:
                    break
                block = padded_y[i*8:(i+1)*8, j*8:(j+1)*8]
                dct_block = cv2.dct(block)
                coeff = dct_block[4, 4]
                val = round(coeff / Q)
                extracted_bits.append(abs(int(val)) % 2)
            if len(extracted_bits) >= 32:
                break

        if len(extracted_bits) < 32:
             raise ValueError("Failed to extract length header.")
             
        length_bytes = cls._from_bits(np.array(extracted_bits, dtype=np.uint8))
        payload_len = np.frombuffer(length_bytes, dtype='>u4')[0]

        total_bits = 32 + payload_len * 8
        
        if total_bits > blocks_h * blocks_w:
             raise ValueError("Corrupt header, calculated capacity exceeds image.")

        # Read the rest
        extracted_bits = []
        bit_idx = 0
        for i in range(blocks_h):
            for j in range(blocks_w):
                if bit_idx >= total_bits:
                    break
                block = padded_y[i*8:(i+1)*8, j*8:(j+1)*8]
                dct_block = cv2.dct(block)
                coeff = dct_block[4, 4]
                val = round(coeff / Q)
                extracted_bits.append(abs(int(val)) % 2)
                bit_idx += 1

        payload_bits = np.array(extracted_bits[32:], dtype=np.uint8)
        encrypted_payload = cls._from_bits(payload_bits)

        salt = b'StegXtreme_Image'
        key = derive_key(password, salt)
        
        try:
             decrypted_payload = aes_decrypt(encrypted_payload, key)
             return decrypted_payload
        except Exception as e:
             raise ValueError("Decryption failed") from e
