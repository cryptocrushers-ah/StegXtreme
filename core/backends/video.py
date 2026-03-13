import cv2
import numpy as np
import os
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

class VideoBackend:
    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload_bits, password: str) -> str:
        """
        Embeds a payload into the cover video and saves it to out_path.
        A very simple LSB implementation for the first frame is used here as a placeholder for robustness.
        In a real scenario, an advanced steganography approach would be used.
        """
        cap = cv2.VideoCapture(cover_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {cover_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'FFV1') # Lossless codec is critical for stego

        out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

        # Encrypt the payload and convert to bits
        salt = b'StegXtreme_Video' # Fixed salt or stored in metadata
        key = derive_key(password, salt)
        # payload_bits is likely numpy array or bytes. if bytes, encrypt it
        if isinstance(payload_bits, bytes):
             encrypted_payload = aes_encrypt(payload_bits, key)
             # Convert to bits
             bits = np.unpackbits(np.frombuffer(encrypted_payload, dtype=np.uint8))
        else:
             # Just a simplified demonstration
             bits = payload_bits
             
        # Embed bits and lengths in the first frame (naive LSB)
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx == 0 and len(bits) > 0:
                # Store length first (32 bits)
                length_bits = np.unpackbits(np.array([len(bits)], dtype='>u4').view(np.uint8))
                all_bits = np.concatenate((length_bits, bits))
                
                # Flatten frame to 1D
                flat_frame = frame.flatten()
                
                if len(all_bits) > len(flat_frame):
                     raise ValueError("Payload too large for a single frame.")
                
                # Zero out LSB and embed
                flat_frame[:len(all_bits)] &= 0xFE
                flat_frame[:len(all_bits)] |= all_bits
                
                frame = flat_frame.reshape(frame.shape)

            out.write(frame)
            frame_idx += 1

        cap.release()
        out.release()
        return out_path

    @classmethod
    def extract(cls, stego_path: str, password: str) -> bytes:
        """
        Extracts the payload from the stego video.
        """
        cap = cv2.VideoCapture(stego_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open stego video: {stego_path}")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError("Stego video is empty.")

        flat_frame = frame.flatten()
        
        # Read length (32 bits)
        length_bits = flat_frame[:32] & 1
        length_bytes = np.packbits(length_bits)
        payload_len = np.frombuffer(length_bytes, dtype='>u4')[0]
        
        # Read payload
        extracted_bits = flat_frame[32:32+payload_len] & 1
        extracted_bytes = np.packbits(extracted_bits).tobytes()
        
        salt = b'StegXtreme_Video'
        key = derive_key(password, salt)
        
        try:
             decrypted_payload = aes_decrypt(extracted_bytes, key)
             return decrypted_payload
        except Exception as e:
             raise ValueError("Decryption failed. Incorrect password?") from e
