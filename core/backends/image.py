import cv2
import numpy as np
import os
from core.compute.auth import sign_and_embed
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt
from core.compute.auth import sign_and_embed
from core.neural.registry import _auth_private_key


class ImageBackend:
    # Mid-frequency coefficients for DCT
    DCT_COEFFS = [(4, 4), (3, 4), (4, 3), (3, 3), (5, 5), (5, 4), (4, 5), (2, 5), (5, 2)]

    @classmethod
    def _to_bits(cls, data: bytes) -> np.ndarray:
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

    @classmethod
    def _from_bits(cls, bits: np.ndarray) -> bytes:
        return np.packbits(bits).tobytes()

    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload: bytes, password: str, algorithm: str = "default") -> str:
        img = cv2.imread(cover_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot open image: {cover_path}")

        salt = b'StegXtreme_Image'
        key = derive_key(password, salt)
        encrypted_payload = aes_encrypt(payload, key)
        
        # Convert payload to bits
        payload_bits = cls._to_bits(encrypted_payload)
        payload_bit_len = len(payload_bits)
        
        # 32-bit length header (stores BIT COUNT)
        length_bytes = np.array([payload_bit_len], dtype='>u4').view(np.uint8)
        
        all_bits = np.concatenate((
            cls._to_bits(length_bytes.tobytes()),
            payload_bits
        ))

        # Authenticity signing — auto sign every embed
        sign_and_embed(out_path, _auth_private_key, out_path)

        if algorithm == "lsb":
             return cls._embed_lsb(img, out_path, all_bits)
        else: # default to dct
             return cls._embed_dct(img, out_path, all_bits)
        
        

    @classmethod
    def _embed_lsb(cls, img, out_path, all_bits):
        h, w, c = img.shape
        max_capacity = h * w * c
        if len(all_bits) > max_capacity:
            raise ValueError(f"Payload too large for LSB. Max capacity {max_capacity} bits, payload {len(all_bits)} bits.")

        # Make a copy to avoid modifying the original image in place if it's used elsewhere
        stego_img = img.copy()
        
        # Flatten the image and payload bits
        flat_img = stego_img.flatten()
        
        # Clear the LSBs of the image pixels where bits will be embedded
        flat_img[:len(all_bits)] &= 0xFE
        # Set the LSBs with the payload bits
        flat_img[:len(all_bits)] |= all_bits
        
        # Reshape back to image dimensions
        stego_img = flat_img.reshape(img.shape)
        cv2.imwrite(out_path, stego_img)
        return out_path

    @classmethod
    def _embed_dct(cls, img, out_path, all_bits):
        # Existing DCT and Multi-channel logic goes here
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        Q = 10.0
        coeffs = cls.DCT_COEFFS
        
        h, w = ycrcb.shape[:2]
        h_pad = h + (8 - h % 8) % 8
        w_pad = w + (8 - w % 8) % 8
        blocks_h, blocks_w = h_pad // 8, w_pad // 8
        
        max_capacity = blocks_h * blocks_w * 3 * len(coeffs)
        if len(all_bits) > max_capacity:
            raise ValueError(f"Payload too large for DCT. Max capacity {max_capacity} bits, payload {len(all_bits)} bits.")

        bit_idx = 0
        for channel_idx in range(3):
            channel_data = ycrcb[:, :, channel_idx].astype(np.float32)
            padded_channel = np.zeros((h_pad, w_pad), dtype=np.float32)
            padded_channel[:h, :w] = channel_data
            
            for i in range(blocks_h):
                for j in range(blocks_w):
                    if bit_idx >= len(all_bits): break
                    block = padded_channel[i*8:(i+1)*8, j*8:(j+1)*8]
                    dct_block = cv2.dct(block)
                    for row, col in coeffs:
                        if bit_idx >= len(all_bits): break
                        val = round(dct_block[row, col] / Q)
                        if val % 2 != all_bits[bit_idx]:
                            val += 1 if all_bits[bit_idx] == 1 else -1
                        dct_block[row, col] = val * Q
                        bit_idx += 1
                    padded_channel[i*8:(i+1)*8, j*8:(j+1)*8] = cv2.idct(dct_block)
                if bit_idx >= len(all_bits): break
            ycrcb[:, :, channel_idx] = np.clip(padded_channel[:h, :w], 0, 255).astype(np.uint8)
            if bit_idx >= len(all_bits): break

        stego_img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        cv2.imwrite(out_path, stego_img)
        return out_path

    @classmethod
    def extract(cls, stego_path: str, password: str, algorithm: str = "default") -> bytes:
        img = cv2.imread(stego_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Cannot open stego image: {stego_path}")

        def get_all_bits(target_count):
            if algorithm == "lsb":
                return cls._extract_lsb_bits(img, target_count)
            else: # default to dct
                return cls._extract_dct_bits(img, target_count)

        # Read 32-bit length header
        length_header_bits = get_all_bits(32)
        if len(length_header_bits) < 32:
             raise ValueError("Failed to extract length header. Image capacity mismatch or incorrect algorithm.")
             
        payload_len = np.frombuffer(cls._from_bits(np.array(length_header_bits, dtype=np.uint8)), dtype='>u4')[0]

        total_bits_needed = 32 + payload_len
        all_extracted_bits = get_all_bits(total_bits_needed)
        
        if len(all_extracted_bits) < total_bits_needed:
             raise ValueError("Failed to extract full payload bits. Image capacity mismatch or incorrect algorithm.")

        encrypted_payload = cls._from_bits(np.array(all_extracted_bits[32:], dtype=np.uint8))
        salt = b'StegXtreme_Image'
        key = derive_key(password, salt)
        
        try:
             return aes_decrypt(encrypted_payload, key)
        except Exception as e:
             raise ValueError("Decryption failed. Incorrect password or algorithm choice.") from e

    @classmethod
    def _extract_lsb_bits(cls, img, count):
        # Flatten the image and extract the LSB of each pixel
        flat_img = img.flatten()
        if len(flat_img) < count:
            raise ValueError(f"Not enough pixels in image to extract {count} bits using LSB.")
        return (flat_img[:count] & 1).tolist()

    @classmethod
    def _extract_dct_bits(cls, img, count):
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        h, w = ycrcb.shape[:2]
        h_pad = h + (8 - h % 8) % 8
        w_pad = w + (8 - w % 8) % 8
        blocks_h, blocks_w = h_pad // 8, w_pad // 8
        Q, coeffs = 10.0, cls.DCT_COEFFS
        bits = []
        
        # Loop over channels, blocks, and coefficients to extract bits
        for c_idx in range(3):
            ch_data = ycrcb[:, :, c_idx].astype(np.float32)
            # Pad for reading
            padded_ch = np.zeros((h_pad, w_pad), dtype=np.float32)
            padded_ch[:h, :w] = ch_data
            
            for i in range(blocks_h):
                for j in range(blocks_w):
                    block = padded_ch[i*8:(i+1)*8, j*8:(j+1)*8]
                    dct_block = cv2.dct(block)
                    for r, c in coeffs:
                        # Extract the LSB of the rounded quantized DCT coefficient
                        bits.append(abs(int(round(dct_block[r, c] / Q))) % 2)
                        if len(bits) >= count:
                            return bits
        return bits

