import cv2
import numpy as np
import os
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

class VideoBackend:
    @classmethod
        # Enforce .avi for lossless FFV1
        if not out_path.lower().endswith('.avi'):
            out_path = os.path.splitext(out_path)[0] + '.avi'

        cap = cv2.VideoCapture(cover_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {cover_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Use FFV1 (Lossless) - AVI container is best for this
        fourcc = cv2.VideoWriter_fourcc(*'FFV1') 
        out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            # Fallback if FFV1 is not available, though we should prefer it
            fourcc = cv2.VideoWriter_fourcc(*'XVID') 
            out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
            if not out.isOpened():
                 raise ValueError("Could not initialize video writer. Check codecs.")

        salt = b'StegXtreme_Video'
        key = derive_key(password, salt)
        if isinstance(payload, bytes):
             encrypted_payload = aes_encrypt(payload, key)
             bits = np.unpackbits(np.frombuffer(encrypted_payload, dtype=np.uint8))
        else:
             bits = payload
             
        # Length (32 bits) + payload
        length_bits = np.unpackbits(np.array([len(bits)], dtype='>u4').view(np.uint8))
        all_bits = np.concatenate((length_bits, bits))
        
        # Dispatch based on algorithm
        # For video, "default" / "temporal" uses 1 spatial LSB across frames
        # "lsb" will use all 3 spatial LSBs (R, G, B) across frames
        bits_per_pixel = 1 if algorithm != "lsb" else 3 
        
        capacity = width * height * 3 * total_frames * (bits_per_pixel // 3 + 1) # Simplification
        # Actually, let's just use 1 bit per pixel channel if lsb, or 1 bit per pixel if default
        # If lsb: 3 bits per pixel (1 per RGB). If default: 1 bit per pixel (on Blue channel maybe? No, let's keep it simple)
        # Re-simplifying for the demo/project:
        if algorithm == "lsb":
             max_capacity = width * height * 3 * total_frames
        else:
             max_capacity = width * height * total_frames # 1 bit per pixel
             
        if len(all_bits) > max_capacity:
             raise ValueError(f"Payload too large. Max capacity is {max_capacity} bits, required {len(all_bits)} bits.")

        bit_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if bit_idx < len(all_bits):
                flat_frame = frame.flatten()
                # If algorithm is default, we only use every 3rd element (one channel)?
                # No, let's just use the first N elements of the flattened frame (which is RGB list)
                # If algorithm is default, we use 1 bit per pixel (every 3 elements)
                # If algorithm is lsb, we use 3 bits per pixel (every 1 element)
                
                if algorithm == "lsb":
                    bits_to_embed = min(len(flat_frame), len(all_bits) - bit_idx)
                    flat_frame[:bits_to_embed] &= 0xFE
                    flat_frame[:bits_to_embed] |= all_bits[bit_idx : bit_idx + bits_to_embed]
                    bit_idx += bits_to_embed
                else:
                    # Default: 1 bit per pixel (assume height*width pixels)
                    # We'll use the first channel (B) of each pixel
                    pixel_count = width * height
                    bits_to_embed = min(pixel_count, (len(all_bits) - bit_idx))
                    # every 3rd element is B
                    for i in range(bits_to_embed):
                        flat_frame[i*3] &= 0xFE
                        flat_frame[i*3] |= all_bits[bit_idx]
                        bit_idx += 1
                
                frame = flat_frame.reshape(frame.shape)
            out.write(frame)

        cap.release()
        out.release()
        return out_path

    @classmethod
    def extract(cls, stego_path: str, password: str, algorithm: str = "default") -> bytes:
        cap = cv2.VideoCapture(stego_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open stego video: {stego_path}")

        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Step 1: Read the 32-bit length header
        # We need to read it using the SAME STRATEGY as embedding
        length_bits = []
        bit_idx = 0
        
        while len(length_bits) < 32:
            ret, frame = cap.read()
            if not ret: break
            flat_frame = frame.flatten()
            if algorithm == "lsb":
                to_read = min(len(flat_frame), 32 - len(length_bits))
                length_bits.extend((flat_frame[:to_read] & 1).tolist())
            else:
                to_read = min(width * height, 32 - len(length_bits))
                for i in range(to_read):
                    length_bits.append(flat_frame[i*3] & 1)
        
        if len(length_bits) < 32:
            cap.release()
            raise ValueError("Failed to extract length header.")
            
        payload_len = np.frombuffer(np.packbits(length_bits), dtype='>u4')[0]
        total_bits = 32 + payload_len
        
        all_bits = np.zeros(total_bits, dtype=np.uint8)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        bit_idx = 0
        while bit_idx < total_bits:
            ret, frame = cap.read()
            if not ret: break
            flat_frame = frame.flatten()
            if algorithm == "lsb":
                bits_to_read = min(len(flat_frame), total_bits - bit_idx)
                all_bits[bit_idx : bit_idx + bits_to_read] = flat_frame[:bits_to_read] & 1
                bit_idx += bits_to_read
            else:
                bits_to_read = min(width * height, total_bits - bit_idx)
                for i in range(bits_to_read):
                    all_bits[bit_idx] = flat_frame[i*3] & 1
                    bit_idx += 1
            
        cap.release()
        
        if bit_idx < total_bits:
             raise ValueError("Failed to extract full payload bits.")

        extracted_bytes = np.packbits(all_bits[32:]).tobytes()
        salt = b'StegXtreme_Video'
        key = derive_key(password, salt)
        
        try:
             return aes_decrypt(extracted_bytes, key)
        except Exception as e:
             raise ValueError("Decryption failed. Ensure the same algorithm is used and the carrier file wasn't re-encoded (lossy conversion).") from e
